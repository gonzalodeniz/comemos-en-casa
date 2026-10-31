"""Shared recipe catalog API."""
import hashlib, os, shutil, unicodedata
from pathlib import Path
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.auth import ActiveSession, get_active_session, require_csrf
from app.database import get_database_session
import app.meal_planning_api as meal_planning_api
from app.food_images import publication_lock, temporary_path
from app.models import Recipe, RecipeFoodLabel, FoodLabel

router=APIRouter(prefix="/api/v1", tags=["recipes"])

def data_root():
    return meal_planning_api.DATA_ROOT
def canon(v): return unicodedata.normalize("NFC",v).strip().casefold()
def norm(v): return "".join(c for c in unicodedata.normalize("NFD",v.casefold()) if unicodedata.category(c)!="Mn")
def image_url(r): return f"/recipes/{r.id}/image?v={hashlib.sha256(r.image_path.encode()).hexdigest()}" if r.image_path else None
def serialize(r,db):
    fs=db.scalars(select(FoodLabel).join(RecipeFoodLabel).where(RecipeFoodLabel.recipe_id==r.id).order_by(FoodLabel.name_canonical)).all()
    return {"id":str(r.id),"title":r.title,"image_url":image_url(r),"ingredients":r.ingredients,"preparation":r.preparation,"foods":[{"id":str(f.id),"name":f.name} for f in fs]}
def title_conflict(error):
    text=str(error.orig).lower()
    return "uq_recipes_title_canonical" in text or "recipes.title_canonical" in text

def recipe_rank(title, ingredient_text, food_names, query):
    terms = norm(query.strip()).split()
    if not terms:
        return 0, 0, norm(title), canon(title)
    title_text = norm(title)
    food_text = " ".join(norm(name) for name in food_names)
    ingredient_text = norm(ingredient_text or "")
    matches = []
    for term in terms:
        priority = 0 if term in title_text else 1 if term in food_text else 2 if term in ingredient_text else 3
        if priority < 3:
            matches.append(priority)
    if not matches:
        return None
    return min(matches), -len(matches), sum(matches), norm(title), canon(title)

def safe_path(rel):
    p=Path(rel)
    if len(p.parts)!=2 or p.parts[0]!="recetas" or len(p.name)!=37 or not p.name.endswith(".webp") or any(c not in "0123456789abcdef" for c in p.name[:32]):return None
    folder=data_root()/"recetas"; path=data_root()/p
    return None if folder.is_symlink() or path.is_symlink() else path
def publish(session,token):
    src=temporary_path(data_root(),session,token)
    if not src:return None
    folder=data_root()/"recetas";folder.mkdir(mode=0o700,parents=True,exist_ok=True)
    if folder.is_symlink():return None
    target=folder/f"{uuid4().hex}.webp";shutil.copyfile(src,target);os.chmod(target,0o600);src.unlink(missing_ok=True)
    return f"recetas/{target.name}"
def prepare(data,db,session,old=None):
    allowed={"title","ingredients","preparation","food_ids","image_token","remove_image"}
    if set(data)-allowed or not isinstance(data.get("title"),str):raise HTTPException(422,"Invalid recipe")
    title=unicodedata.normalize("NFC",data["title"]).strip()
    if not title or len(title)>150:raise HTTPException(422,"Title must contain 1 to 150 characters")
    key=canon(title)
    statement=select(Recipe).where(Recipe.title_canonical==key)
    if old is not None:statement=statement.where(Recipe.id!=old.id)
    if db.scalar(statement):raise HTTPException(409,"Recipe title already exists")
    raw=data.get("food_ids",[])
    try: ids=[UUID(x) for x in raw] if isinstance(raw,list) and all(isinstance(x,str) for x in raw) else None
    except (ValueError, TypeError, AttributeError): ids=None
    if ids is None or len(ids)!=len(set(ids)) or (ids and len(db.scalars(select(FoodLabel.id).where(FoodLabel.id.in_(ids))).all())!=len(ids)):raise HTTPException(422,"Invalid food associations")
    image_token=data.get("image_token")
    remove_image=data.get("remove_image",False)
    if (image_token is not None and not isinstance(image_token,str)) or not isinstance(remove_image,bool):
        raise HTTPException(422,"Invalid image fields")
    fields={}
    for k in ("ingredients","preparation"):
        val=data.get(k)
        if val is not None and not isinstance(val,str):raise HTTPException(422,"Invalid recipe text")
        fields[k]=val
    image=old.image_path if old else None
    if image_token:
        image=publish(session,image_token)
        if not image:raise HTTPException(422,"Prepared image expired")
    elif remove_image:image=None
    return title,key,ids,fields,image

@router.get("/recipes")
def list_recipes(q:str="",food_id:UUID|None=None,_:ActiveSession=Depends(get_active_session),db:Session=Depends(get_database_session)):
    rows=db.scalars(select(Recipe)).all()
    def rank(r):
        fs=db.scalars(select(FoodLabel).join(RecipeFoodLabel).where(RecipeFoodLabel.recipe_id==r.id)).all()
        if food_id and food_id not in {f.id for f in fs}:return None
        return recipe_rank(r.title,r.ingredients,[f.name for f in fs],q)
    return {"recipes":[serialize(r,db) for r in sorted((x for x in rows if rank(x) is not None),key=rank)]}

@router.get("/recipes/{rid}")
def get_recipe(rid:UUID,_:ActiveSession=Depends(get_active_session),db:Session=Depends(get_database_session)):
    r=db.get(Recipe,rid)
    if not r:raise HTTPException(404,"Recipe not found")
    return {"recipe":serialize(r,db)}

@router.post("/recipes",status_code=201)
def create_recipe(data:dict,request:Request,s:ActiveSession=Depends(get_active_session),db:Session=Depends(get_database_session)):
    require_csrf(request,s)
    with publication_lock(data_root()):
        title,key,ids,fields,image=prepare(data,db,s.session.id)
        r=Recipe(title=title,title_canonical=key,image_path=image,**fields);db.add(r)
        try:
            db.flush()
            db.add_all([RecipeFoodLabel(recipe_id=r.id,food_label_id=i) for i in ids]);db.commit()
        except IntegrityError as e:
            db.rollback()
            if title_conflict(e):raise HTTPException(409,"Recipe title already exists") from e
            raise
        return {"recipe":serialize(r,db)}

@router.patch("/recipes/{rid}")
def update_recipe(rid:UUID,data:dict,request:Request,s:ActiveSession=Depends(get_active_session),db:Session=Depends(get_database_session)):
    require_csrf(request,s)
    with publication_lock(data_root()):
        r=db.get(Recipe,rid)
        if not r:raise HTTPException(404,"Recipe not found")
        title,key,ids,fields,image=prepare(data,db,s.session.id,r);old=r.image_path
        r.title=title;r.title_canonical=key;r.ingredients=fields["ingredients"];r.preparation=fields["preparation"];r.image_path=image
        db.query(RecipeFoodLabel).filter_by(recipe_id=r.id).delete(synchronize_session=False)
        db.add_all([RecipeFoodLabel(recipe_id=r.id,food_label_id=i) for i in ids])
        try:db.commit()
        except IntegrityError as e:
            db.rollback()
            if title_conflict(e):raise HTTPException(409,"Recipe title already exists") from e
            raise
        if old and old!=image:
            p=safe_path(old)
            if p:p.unlink(missing_ok=True)
        return {"recipe":serialize(r,db)}

@router.delete("/recipes/{rid}",status_code=204)
def delete_recipe(rid:UUID,request:Request,response:Response,s:ActiveSession=Depends(get_active_session),db:Session=Depends(get_database_session)):
    require_csrf(request,s)
    with publication_lock(data_root()):
        r=db.get(Recipe,rid)
        if not r:raise HTTPException(404,"Recipe not found")
        image=r.image_path;db.delete(r);db.commit()
        if image:
            p=safe_path(image)
            if p:p.unlink(missing_ok=True)
        response.status_code=204

@router.get("/recipes/{rid}/image")
def recipe_image(rid:UUID,response:Response,_:ActiveSession=Depends(get_active_session),db:Session=Depends(get_database_session)):
    r=db.get(Recipe,rid);p=safe_path(r.image_path) if r and r.image_path else None
    if not p or not p.is_file():raise HTTPException(404,"Image not found")
    return FileResponse(p,media_type="image/webp",headers={"Cache-Control":"private, max-age=3600"})
