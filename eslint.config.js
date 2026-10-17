import js from "@eslint/js";
import globals from "globals";

export default [
  { ignores: ["node_modules/**", "artifacts/**", ".superpowers/**"] },
  js.configs.recommended,
  {
    files: ["src/anthropic_readiness/resources/**/*.js"],
    languageOptions: { globals: globals.browser },
  },
  {
    files: ["tests/**/*.js", "*.config.js"],
    languageOptions: { globals: globals.node },
  },
  {
    files: ["tests/browser/**/*.js"],
    languageOptions: { globals: { ...globals.node, ...globals.browser } },
  },
];
