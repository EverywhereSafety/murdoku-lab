// Every player-facing string goes through t(), so another language is one more JSON file.
import en from "./en.json";

const catalogs = { en };
let current = catalogs.en;

export function setLocale(locale) {
  current = catalogs[locale] || catalogs.en;
}

export function t(key, vars = {}) {
  const template = current[key] ?? catalogs.en[key] ?? key;
  return template.replace(/\{(\w+)\}/g, (_, name) => (name in vars ? String(vars[name]) : `{${name}}`));
}
