const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  // 核心配置：关闭ESLint校验
  lintOnSave: false,
  transpileDependencies: true
})
