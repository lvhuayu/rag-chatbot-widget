/** @type {import('tailwindcss').Config} */
// 仅用于编译首页 public/index.html 所用的 Tailwind 工具类 -> public/styles.css
// 重新编译：npm run build:css
module.exports = {
  content: ['./public/index.html'],
  theme: { extend: {} },
  plugins: [],
};
