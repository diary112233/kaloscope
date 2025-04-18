import {
  continuedIndent,
  foldInside,
  foldNodeProp,
  indentNodeProp,
  LanguageSupport,
  LRLanguage
} from '@codemirror/language';
import { parser } from './jsonc-parser';

/**
 * A language provider that provides JSONC (JSON with comments) parsing.
 */
export const jsoncLanguage = LRLanguage.define({
  name: 'jsonc',
  parser: parser.configure({
    props: [
      indentNodeProp.add({
        Object: continuedIndent({ except: /^\s*}/ }),
        Array: continuedIndent({ except: /^\s*\]/ })
      }),
      foldNodeProp.add({
        'Object Array': foldInside
      })
    ]
  }),
  languageData: {
    closeBrackets: { brackets: ['[', '{', '"'] },
    indentOnInput: /^\s*[}\]]$/
  }
});

/**
 * JSONC (JSON with comments) language support.
 *
 * @returns A language support instance for JSONC.
 */
export function jsonc() {
  return new LanguageSupport(jsoncLanguage);
}
