import { useEffect, useRef, useState } from 'react';

/**
 * CreatableCombobox
 *
 * Props:
 *   label        — field label string
 *   options      — [{ id, label }]  existing items
 *   value        — currently selected id (or null/"")
 *   onChange     — (id) => void
 *   onCreate     — async (name) => { id, label }   called when user confirms create
 *   placeholder  — input placeholder
 *   disabled     — boolean
 */
export default function CreatableCombobox({ label, options = [], value, onChange, onCreate, placeholder = 'Search or type new…', disabled }) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const containerRef = useRef(null);
  const inputRef = useRef(null);

  const selected = options.find((o) => String(o.id) === String(value));
  const displayText = open ? query : (selected?.label ?? '');

  const filtered = query
    ? options.filter((o) => o.label.toLowerCase().includes(query.toLowerCase()))
    : options;

  const exactMatch = options.some((o) => o.label.toLowerCase() === query.toLowerCase());
  const showCreate = query.trim() && !exactMatch && onCreate;

  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
        setQuery('');
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleFocus = () => {
    setOpen(true);
    setQuery('');
  };

  const selectOption = (opt) => {
    onChange(opt.id);
    setOpen(false);
    setQuery('');
  };

  const handleCreate = async () => {
    if (!query.trim() || creating) return;
    setCreating(true);
    try {
      const created = await onCreate(query.trim());
      if (created) {
        onChange(created.id);
        setOpen(false);
        setQuery('');
      }
    } finally {
      setCreating(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered.length === 1) { selectOption(filtered[0]); return; }
      if (showCreate) handleCreate();
    }
    if (e.key === 'Escape') { setOpen(false); setQuery(''); }
  };

  return (
    <div className="form-group" ref={containerRef} style={{ position: 'relative' }}>
      {label && <span className="form-label">{label}</span>}
      <input
        ref={inputRef}
        className="input"
        value={displayText}
        placeholder={placeholder}
        disabled={disabled}
        onFocus={handleFocus}
        onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
        onKeyDown={handleKeyDown}
        autoComplete="off"
      />
      {open && (
        <div className="combobox-dropdown">
          {filtered.length === 0 && !showCreate && (
            <div className="combobox-empty">No results</div>
          )}
          {filtered.map((opt) => (
            <div
              key={opt.id}
              className={`combobox-option${String(opt.id) === String(value) ? ' combobox-option--selected' : ''}`}
              onMouseDown={(e) => { e.preventDefault(); selectOption(opt); }}
            >
              {opt.label}
            </div>
          ))}
          {showCreate && (
            <div
              className="combobox-option combobox-option--create"
              onMouseDown={(e) => { e.preventDefault(); handleCreate(); }}
            >
              {creating ? 'Creating…' : `Create "${query.trim()}"`}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
