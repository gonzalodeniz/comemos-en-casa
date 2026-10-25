import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Button, Field, Message, Panel } from "./index";

describe("Button", () => {
  it("defaults to a primary button of type button", () => {
    const markup = renderToStaticMarkup(<Button>Save</Button>);

    expect(markup).toBe('<button type="button" class="ui-button">Save</button>');
  });

  it.each([
    ["secondary", "ui-button secondary"],
    ["danger", "ui-button danger"],
    ["link", "ui-button link-button"],
  ] as const)("maps the %s variant to its class", (variant, className) => {
    expect(renderToStaticMarkup(<Button variant={variant}>x</Button>)).toContain(`class="${className}"`);
  });

  it("allows submit buttons and forwards disabled", () => {
    const markup = renderToStaticMarkup(<Button type="submit" disabled>Go</Button>);

    expect(markup).toContain('type="submit"');
    expect(markup).toContain('disabled=""');
  });
});

describe("Field", () => {
  it("wraps the control in a label and renders the hint when given", () => {
    const markup = renderToStaticMarkup(
      <Field label="Email" hint="We never share it"><input name="email" /></Field>,
    );

    expect(markup).toBe(
      '<label class="ui-field">Email<input name="email"/><small>We never share it</small></label>',
    );
  });

  it("omits the hint element when none is provided", () => {
    expect(renderToStaticMarkup(<Field label="Name"><input /></Field>)).not.toContain("<small>");
  });
});

describe("Panel", () => {
  it("renders a section and only adds narrow when requested", () => {
    expect(renderToStaticMarkup(<Panel>content</Panel>)).toBe('<section class="ui-panel">content</section>');
    expect(renderToStaticMarkup(<Panel narrow>content</Panel>)).toContain('class="ui-panel narrow"');
  });
});

describe("Message", () => {
  it("announces errors as alerts", () => {
    expect(renderToStaticMarkup(<Message tone="error">Failed</Message>)).toBe(
      '<p class="ui-message error" role="alert">Failed</p>',
    );
  });

  it("announces successes as status updates", () => {
    expect(renderToStaticMarkup(<Message tone="success">Saved</Message>)).toBe(
      '<p class="ui-message success" role="status">Saved</p>',
    );
  });
});
