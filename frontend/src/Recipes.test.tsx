import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { linkifyRecipeText } from "./Recipes";

describe("recipe text links", () => {
  it("renders HTTP(S) URLs as safe clickable links and preserves surrounding text", () => {
    const html = renderToStaticMarkup(<p>{linkifyRecipeText("Fuente: https://example.com/receta más pasos")}</p>);
    expect(html).toContain('<a href="https://example.com/receta" target="_blank" rel="noopener noreferrer">https://example.com/receta</a>');
    expect(html).toContain("Fuente: ");
    expect(html).toContain(" más pasos");
  });

  it("does not turn non-HTTP text into a link", () => {
    const html = renderToStaticMarkup(<p>{linkifyRecipeText("ftp://example.com receta")}</p>);
    expect(html).not.toContain("<a ");
    expect(html).toContain("ftp://example.com receta");
  });
});
