module.exports = [
    {
        files: ["frontend/assets/js/**/*.js"],
        languageOptions: {
            ecmaVersion: 2021,
            sourceType: "script",
            globals: {
                console: "readonly",
                document: "readonly",
                fetch: "readonly",
                FileReader: "readonly",
                URL: "readonly",
                window: "readonly",
            },
        },
        rules: {
            "no-unused-vars": ["warn", { args: "none" }],
        },
    },
];
