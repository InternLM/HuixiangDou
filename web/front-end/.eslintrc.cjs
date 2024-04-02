module.exports = {
    root: true,
    parser: '@typescript-eslint/parser',
    env: {
        es6: true,
        browser: true,
        node: true
    },
    extends: [
        'eslint:recommended',
        'plugin:@typescript-eslint/eslint-recommended',
        'plugin:@typescript-eslint/recommended',
        'airbnb',
        'airbnb/hooks',
    ],
    settings: {
        'import/resolver': {
            node: {
                paths: [
                    'src'
                ],
                extensions: [
                    '.js',
                    '.jsx',
                    '.ts',
                    '.tsx'
                ]
            }
        }
    },
    rules: {
        'import/extensions': 'off',
        '@typescript-eslint/no-var-requires': 'off',
        'arrow-body-style': 'off',
        'comma-dangle': 'off',
        'import/no-unresolved': 'off',
        'jsx-a11y/anchor-is-valid': 'off',
        'jsx-a11y/click-events-have-key-events': 'off',
        'jsx-a11y/control-has-associated-label': 'off',
        'jsx-a11y/no-static-element-interactions': 'off',
        'no-console': 'off',
        'no-param-reassign': 'off',
        'no-plusplus': 'off',
        'no-underscore-dangle': 'off',
        'arrow-parens': 'off',
        'react/forbid-prop-types': 'off',
        'react/react-in-jsx-scope': 'off',
        'react/jsx-filename-extension': 'off',
        'react/jsx-props-no-spreading': 'off',
        'react/require-default-props': 'off',
        'react/function-component-definition': 'off',
        'jsx-a11y/alt-text': 'Off',
        'react/jsx-indent': [2, 4],
        'react/jsx-indent-props': [2, 4],
        'react/no-unused-prop-types': 'warn',
        'react/prop-types': 'off',
        'react/destructuring-assignment': 'off',
        'react/no-array-index-key': 'warn',
        eqeqeq: ['error', 'allow-null'],
        'prefer-const': 'warn',
        'array-callback-return': 'warn',
        // https://stackoverflow.com/questions/48391913/eslint-error-cannot-read-property-range-of-null
        'template-curly-spacing': 'off',
        'prefer-destructuring': 'off',
        'guard-for-in': 'warn',
        camelcase: ['warn'],
        'import/prefer-default-export': 'off',
        'no-useless-escape': 'warn',
        'no-unused-expressions': 'warn',
        'no-restricted-syntax': 'off',
        'max-len': ['warn', {
            code: 200
        }],
        'no-shadow': ['warn'],
        indent: ['error', 4, {
            ignoredNodes: ['TemplateLiteral']
        }],
        semi: ['warn', 'always', { omitLastInOneLineBlock: true }],
        'no-proto': 'error',
        // https://github.com/import-js/eslint-plugin-import/issues/653#issuecomment-840228881
        'no-unused-vars': 'off',
        '@typescript-eslint/no-unused-vars': ['warn'],
        'react-hooks/exhaustive-deps': 'warn',
        'class-methods-use-this': 'warn',
        'prefer-promise-reject-errors': 'warn',
        'object-shorthand': 'warn',
        'import/no-extraneous-dependencies': 'off',
        '@typescript-eslint/no-namespace': 'off',
        'no-restricted-operator': 'off',
    }
};
