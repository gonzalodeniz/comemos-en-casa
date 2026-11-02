# Verifica la publicación, inspección y limpieza de imágenes de alimentos.
import asyncio

import pytest

from app.models import FoodLabel


from meal_planning_test_support import meal_database


def test_managed_image_rejects_absolute_traversal_and_symlinks(tmp_path, monkeypatch):
    import app.meal_planning_api as api

    monkeypatch.setattr(api, "DATA_ROOT", tmp_path)
    folder = tmp_path / "comidas"
    folder.mkdir()
    name = "a" * 32 + ".webp"
    image = folder / name
    image.write_bytes(b"image")
    assert api._managed_food_image_path(f"comidas/{name}") == image
    assert api._managed_food_image_path(str(image)) is None
    assert api._managed_food_image_path(f"comidas/../comidas/{name}") is None
    image.unlink()
    image.symlink_to(tmp_path / "outside")
    assert api._managed_food_image_path(f"comidas/{name}") is None

def test_cleanup_failure_does_not_raise(tmp_path, monkeypatch, caplog):
    import app.meal_planning_api as api
    from pathlib import Path

    monkeypatch.setattr(api, "DATA_ROOT", tmp_path)
    (tmp_path / "comidas").mkdir()
    def fail_unlink(self, *args, **kwargs):
        raise PermissionError("denied")
    monkeypatch.setattr(Path, "unlink", fail_unlink)
    api._remove_food_image("comidas/" + "a" * 32 + ".webp")
    assert "food_image_cleanup_failed" in caplog.text

def test_orphan_inspection_is_advisory_and_preserves_files(meal_database, tmp_path):
    import os
    from app.food_images import ORPHAN_GRACE_SECONDS, inspect_possible_orphans

    folder = tmp_path / "comidas"
    folder.mkdir()
    active, orphan, fresh = [folder / (character * 32 + ".webp") for character in "abc"]
    for image in (active, orphan, fresh):
        image.write_bytes(b"image")
    now = 2_000_000.0
    for image in (active, orphan):
        os.utime(image, (now - ORPHAN_GRACE_SECONDS - 1,) * 2)
    os.utime(fresh, (now,) * 2)
    with meal_database() as db:
        db.add(FoodLabel(code="active-image", name="Active", image_path=f"comidas/{active.name}"))
        db.commit()
        assert inspect_possible_orphans(tmp_path, db, now=now) == [f"comidas/{orphan.name}"]
    assert all(image.exists() for image in (active, orphan, fresh))

def test_reconciliation_deletes_only_old_unreferenced_files(meal_database, tmp_path):
    import os
    from app.food_images import ORPHAN_GRACE_SECONDS, reconcile_orphans

    folder = tmp_path / "comidas"
    folder.mkdir()
    active, orphan, fresh = [folder / (character * 32 + ".webp") for character in "abc"]
    now = 2_000_000.0
    for image in (active, orphan, fresh):
        image.write_bytes(b"image")
    for image in (active, orphan):
        os.utime(image, (now - ORPHAN_GRACE_SECONDS - 1,) * 2)
    os.utime(fresh, (now,) * 2)
    with meal_database() as db:
        db.add(FoodLabel(code="protected", name="Protected", image_path=f"comidas/{active.name}"))
        db.commit()
    assert reconcile_orphans(tmp_path, meal_database, now=now) == [f"comidas/{orphan.name}"]
    assert active.exists() and fresh.exists() and not orphan.exists()
    assert reconcile_orphans(tmp_path, meal_database, now=now) == []

def test_reconciliation_waits_for_publication_commit(meal_database, tmp_path):
    import os
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from app.food_images import ORPHAN_GRACE_SECONDS, publication_lock, reconcile_orphans

    folder = tmp_path / "comidas"
    folder.mkdir()
    image = folder / ("a" * 32 + ".webp")
    image.write_bytes(b"image")
    now = 2_000_000.0
    os.utime(image, (now - ORPHAN_GRACE_SECONDS - 1,) * 2)
    started = threading.Event()
    def reconcile():
        started.set()
        return reconcile_orphans(tmp_path, meal_database, now=now)
    with ThreadPoolExecutor() as executor:
        with publication_lock(tmp_path):
            future = executor.submit(reconcile)
            assert started.wait(5)
            with meal_database() as db:
                db.add(FoodLabel(code="in-flight", name="In flight", image_path=f"comidas/{image.name}"))
                db.commit()
        assert future.result(timeout=5) == []
    assert image.exists()

def test_async_publication_lock_keeps_event_loop_responsive(tmp_path):
    from app.food_images import async_publication_lock, publication_lock

    async def check():
        entered = asyncio.Event()
        async def waiter():
            async with async_publication_lock(tmp_path):
                entered.set()
        with publication_lock(tmp_path):
            task = asyncio.create_task(waiter())
            await asyncio.sleep(0.12)
            assert not entered.is_set()
        await asyncio.wait_for(task, 2)
        assert entered.is_set()
    asyncio.run(check())

def test_manual_reconciliation_requires_explicit_confirmation(meal_database, tmp_path, monkeypatch):
    import os
    import sys
    import app.database as database
    from app.food_images import main

    monkeypatch.setenv("APP_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(database, "SessionFactory", meal_database)
    monkeypatch.setattr(sys, "argv", ["food_images"])
    with pytest.raises(SystemExit):
        main()
    folder = tmp_path / "comidas"
    folder.mkdir()
    image = folder / ("a" * 32 + ".webp")
    image.write_bytes(b"image")
    os.utime(image, (1, 1))
    monkeypatch.setattr(sys, "argv", ["food_images", "--confirm-coordinated-storage"])
    main()
    assert not image.exists()

def test_app_lifespan_does_not_schedule_orphan_reconciliation():
    import ast
    import inspect
    import textwrap
    import app.main as main_module

    for function in (main_module.lifespan, main_module._cleanup_food_image_temporaries):
        tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        assert "reconcile_orphans" not in names

def test_reconciliation_database_failure_preserves_files(tmp_path):
    from app.food_images import reconcile_orphans
    folder = tmp_path / "comidas"
    folder.mkdir()
    image = folder / ("a" * 32 + ".webp")
    image.write_bytes(b"image")
    def broken_factory():
        raise RuntimeError("database unavailable")
    with pytest.raises(RuntimeError, match="database unavailable"):
        reconcile_orphans(tmp_path, broken_factory)
    assert image.exists()

def test_reconciliation_rejects_symlinked_directory(tmp_path):
    from app.food_images import reconcile_orphans
    outside = tmp_path / "outside"
    outside.mkdir()
    image = outside / ("a" * 32 + ".webp")
    image.write_bytes(b"image")
    (tmp_path / "comidas").symlink_to(outside, target_is_directory=True)
    class EmptyDatabase:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def scalars(self, _query): return iter(())
    with pytest.raises(OSError):
        reconcile_orphans(tmp_path, EmptyDatabase)
    assert image.exists()

def test_reconciliation_propagates_unlink_failure(meal_database, tmp_path, monkeypatch):
    import os
    from app.food_images import reconcile_orphans
    folder = tmp_path / "comidas"
    folder.mkdir()
    image = folder / ("a" * 32 + ".webp")
    image.write_bytes(b"image")
    os.utime(image, (1, 1))
    def fail(*args, **kwargs):
        raise PermissionError("unlink denied")
    monkeypatch.setattr(os, "unlink", fail)
    with pytest.raises(PermissionError, match="unlink denied"):
        reconcile_orphans(tmp_path, meal_database, now=2_000_000)
    assert image.exists()

def test_orphan_inspection_fails_closed_on_database_failure(tmp_path):
    from app.food_images import inspect_possible_orphans

    class BrokenDatabase:
        def scalars(self, _query):
            raise RuntimeError("database unavailable")

    with pytest.raises(RuntimeError, match="database unavailable"):
        inspect_possible_orphans(tmp_path, BrokenDatabase())

def test_orphan_inspection_rejects_symlinked_storage(tmp_path):
    from app.food_images import inspect_possible_orphans

    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "comidas").symlink_to(outside, target_is_directory=True)

    class EmptyDatabase:
        def scalars(self, _query):
            return iter(())

    with pytest.raises(OSError, match="Unsafe image storage"):
        inspect_possible_orphans(tmp_path, EmptyDatabase())

def test_orphan_inspection_propagates_file_metadata_errors(tmp_path, monkeypatch):
    from pathlib import Path
    from app.food_images import inspect_possible_orphans

    folder = tmp_path / "comidas"
    folder.mkdir()
    image = folder / ("a" * 32 + ".webp")
    image.write_bytes(b"image")
    original_lstat = Path.lstat

    def fail_image_lstat(path):
        if path == image:
            raise PermissionError("metadata unavailable")
        return original_lstat(path)

    class EmptyDatabase:
        def scalars(self, _query):
            return iter(())

    monkeypatch.setattr(Path, "lstat", fail_image_lstat)
    with pytest.raises(PermissionError, match="metadata unavailable"):
        inspect_possible_orphans(tmp_path, EmptyDatabase())
    assert image.read_bytes() == b"image"

def test_orphan_inspection_never_deletes_publication_after_snapshot(meal_database, tmp_path):
    import os
    from concurrent.futures import ThreadPoolExecutor
    from app.food_images import ORPHAN_GRACE_SECONDS, inspect_possible_orphans

    folder = tmp_path / "comidas"
    folder.mkdir()
    image = folder / ("a" * 32 + ".webp")
    image.write_bytes(b"image")
    now = 2_000_000.0
    os.utime(image, (now - ORPHAN_GRACE_SECONDS - 1,) * 2)

    def commit_reference():
        with meal_database() as writer:
            writer.add(FoodLabel(code="concurrent-image", name="Concurrent", image_path=f"comidas/{image.name}"))
            writer.commit()

    with meal_database() as reader, ThreadPoolExecutor(max_workers=1) as executor:
        class ConcurrentPublication:
            committed = False

            def scalars(self, query):
                snapshot = list(reader.scalars(query))
                if not self.committed:
                    self.committed = True
                    executor.submit(commit_reference).result(timeout=5)
                return iter(snapshot)

        assert inspect_possible_orphans(tmp_path, ConcurrentPublication(), now=now) == [f"comidas/{image.name}"]
    assert image.exists()  # A stale candidate is never treated as deletion authority.
