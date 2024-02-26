# 1. 命令
## 安装依赖
npm install

## 开发
npm run dev

## build
npm run build
<p>针对不同的环境打包命令不同，比如线上环境的命令<code>npm run build:aliyun-prod</code></p>

## preview
npm run preview
<p>这是vite项目特有的命令，因为vite的serve和build出的代码不一致，上线前需要用preview检测打包结果是否和serve一致</p>

## mock
npm run mock

# 2. Ability config
<div>当前模板支持动态配置能力</div>
<div><strong>src/config/auth.ts</strong>： 支持是否开启该功能（default false）clientId, 接口白名单与网页白名单</div>
<div><strong>src/config/log.ts</strong>： 支持是否开启该功能（default false）ga4 measurement id</div>
<div><strong>src/config/base-url.ts</strong>： 各个环境接口访问host和api prefix</div>

<p>更多细节请查看配置文件注释</p>

