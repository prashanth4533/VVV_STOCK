import * as XLSX from 'xlsx';

/**
 * excel.js — shared Excel helpers for bulk import/export.
 * Uses the existing `xlsx` dependency (already used in App.jsx for export).
 */

/** Download an array of row objects as an .xlsx file. */
export function downloadSheet(rows, sheetName, fileName) {
  const wb = XLSX.utils.book_new();
  const ws = XLSX.utils.json_to_sheet(rows);
  XLSX.utils.book_append_sheet(wb, ws, sheetName);
  XLSX.writeFile(wb, fileName);
}

/**
 * Download a template with the given headers and one example row.
 * @param {string[]} headers
 * @param {object} example — example values keyed by header
 */
export function downloadTemplate(headers, example, sheetName, fileName) {
  const wb = XLSX.utils.book_new();
  const ws = XLSX.utils.json_to_sheet([example], { header: headers });
  XLSX.utils.book_append_sheet(wb, ws, sheetName);
  XLSX.writeFile(wb, fileName);
}

/**
 * Parse the first sheet of an uploaded file into an array of row objects.
 * Header cells are trimmed and lower-cased so column matching is forgiving.
 * @returns {Promise<Array<object>>}
 */
export function parseSheet(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error('Could not read the file.'));
    reader.onload = (e) => {
      try {
        const wb = XLSX.read(e.target.result, { type: 'array' });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const raw = XLSX.utils.sheet_to_json(ws, { defval: '' });
        const rows = raw.map((r) => {
          const norm = {};
          Object.keys(r).forEach((k) => {
            norm[String(k).trim().toLowerCase()] = r[k];
          });
          return norm;
        });
        resolve(rows);
      } catch (err) {
        reject(new Error('Invalid Excel file. Please use the provided template.'));
      }
    };
    reader.readAsArrayBuffer(file);
  });
}
