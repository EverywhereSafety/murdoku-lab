// Every player-facing string goes through t(), so another language is one more JSON file.
import en from "./en.json";

const catalogs = { en };
let current = catalogs.en;
let plurals = new Intl.PluralRules("en");

export function setLocale(locale) {
  current = catalogs[locale] || catalogs.en;
  plurals = new Intl.PluralRules(catalogs[locale] ? locale : "en");
}

// A numeric `n` picks a plural form when the catalog has one: "reveal.hints.one", ".other".
export function t(key, vars = {}) {
  const form = typeof vars.n === "number" ? `${key}.${plurals.select(vars.n)}` : null;
  const template = (form && (current[form] ?? catalogs.en[form])) ?? current[key] ?? catalogs.en[key] ?? key;
  return template.replace(/\{(\w+)\}/g, (_, name) => (name in vars ? String(vars[name]) : `{${name}}`));
}
