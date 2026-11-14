// Editing Markdown in a text box with a preview, for item descriptions and docs.
//
// `save(draft, base)` sends the text and the text the edit started from, and throws the write
// API's error. If the text changed on disk meanwhile, the server answers 409 with the text on
// disk, and both versions are shown to choose from. Nothing is silently overwritten.
import { html, useState } from "./lib.js";
import { Markdown } from "./markdown.js";

export function MarkdownEditor({ id, text, noun, items, save, close, className = "" }) {
  const [edit, setEdit] = useState({ draft: text, base: text, preview: false, conflict: null, error: "", saving: false });
  const update = (changes) => setEdit((current) => ({ ...current, ...changes }));

  async function submit(draft, base) {
    update({ saving: true, error: "" });
    try {
      await save(draft, base);
      close();
    } catch (problem) {
      if (problem.status === 409) update({ saving: false, conflict: problem.answer.current });
      else update({ saving: false, error: problem.message });
    }
  }

  if (edit.conflict !== null) {
    return html`<section class=${`item-section conflict ${className}`} aria-labelledby=${`${id}-conflict`}>
      <p class="notice warn-note" id=${`${id}-conflict`} role="alert">
        The ${noun} changed on disk while you were editing it. Choose which to keep.
      </p>
      <div class="versions">
        <div><h3 class="field-label">Yours</h3><pre class="version">${edit.draft}</pre></div>
        <div><h3 class="field-label">On disk now</h3><pre class="version">${edit.conflict}</pre></div>
      </div>
      ${edit.error ? html`<p class="notice error" role="alert">${edit.error}</p>` : null}
      <div class="edit-buttons">
        <button class="btn primary" type="button" disabled=${edit.saving}
          onClick=${() => submit(edit.draft, edit.conflict)}>Keep mine</button>
        <button class="btn" type="button" disabled=${edit.saving} onClick=${close}>Use the one on disk</button>
        <button class="btn" type="button" disabled=${edit.saving}
          onClick=${() => update({ base: edit.conflict, conflict: null })}>Edit mine</button>
      </div>
    </section>`;
  }

  const changed = edit.draft !== edit.base;
  return html`<section class=${`item-section editing ${className}`}>
    <div class="tabs" role="tablist" aria-label=${noun}>
      <button type="button" role="tab" aria-selected=${!edit.preview} onClick=${() => update({ preview: false })}>Write</button>
      <button type="button" role="tab" aria-selected=${edit.preview} onClick=${() => update({ preview: true })}>Preview</button>
    </div>
    ${edit.preview
      ? html`<div class="preview">${edit.draft.trim() ? html`<${Markdown} text=${edit.draft} items=${items} />` : html`<p class="empty">Nothing to preview.</p>`}</div>`
      : html`<label class="visually-hidden" for=${id}>The ${noun}, in Markdown</label>
        <textarea id=${id} class="textarea" value=${edit.draft} disabled=${edit.saving}
          ref=${(element) => element && !element.dataset.focused && ((element.dataset.focused = "1"), element.focus())}
          onInput=${(event) => update({ draft: event.currentTarget.value })}
          onKeyDown=${(event) => {
            if (event.key === "Escape" && !changed) {
              event.preventDefault();
              close();
            } else if (event.key === "Escape") {
              event.preventDefault(); // keep the panel open; Cancel throws the text away
            } else if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
              event.preventDefault();
              submit(edit.draft, edit.base);
            }
          }}></textarea>`}
    ${edit.error ? html`<p class="notice error" role="alert">${edit.error}</p>` : null}
    <div class="edit-buttons">
      <button class="btn primary" type="button" disabled=${edit.saving || !changed}
        onClick=${() => submit(edit.draft, edit.base)}>${edit.saving ? "Saving…" : "Save"}</button>
      <button class="btn" type="button" disabled=${edit.saving} onClick=${close}>Cancel</button>
      <span class="small muted">Markdown. Ctrl+Enter saves.</span>
    </div>
  </section>`;
}
