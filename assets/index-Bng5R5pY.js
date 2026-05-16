var tB=Object.defineProperty;var nB=(e,t,n)=>t in e?tB(e,t,{enumerable:!0,configurable:!0,writable:!0,value:n}):e[t]=n;var Py=(e,t,n)=>nB(e,typeof t!="symbol"?t+"":t,n);function rB(e,t){for(var n=0;n<t.length;n++){const r=t[n];if(typeof r!="string"&&!Array.isArray(r)){for(const a in r)if(a!="default"&&!(a in e)){const l=Object.getOwnPropertyDescriptor(r,a);l&&Object.defineProperty(e,a,l.get?l:{enumerable:!0,get:()=>r[a]})}}}return Object.freeze(Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}))}(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const a of document.querySelectorAll('link[rel="modulepreload"]'))r(a);new MutationObserver(a=>{for(const l of a)if(l.type==="childList")for(const s of l.addedNodes)s.tagName==="LINK"&&s.rel==="modulepreload"&&r(s)}).observe(document,{childList:!0,subtree:!0});function n(a){const l={};return a.integrity&&(l.integrity=a.integrity),a.referrerPolicy&&(l.referrerPolicy=a.referrerPolicy),a.crossOrigin==="use-credentials"?l.credentials="include":a.crossOrigin==="anonymous"?l.credentials="omit":l.credentials="same-origin",l}function r(a){if(a.ep)return;a.ep=!0;const l=n(a);fetch(a.href,l)}})();var KE=typeof globalThis<"u"?globalThis:typeof window<"u"?window:typeof global<"u"?global:typeof self<"u"?self:{};function Ii(e){return e&&e.__esModule&&Object.prototype.hasOwnProperty.call(e,"default")?e.default:e}var My={exports:{}},hu={};/**
 * @license React
 * react-jsx-runtime.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var GE;function iB(){if(GE)return hu;GE=1;var e=Symbol.for("react.transitional.element"),t=Symbol.for("react.fragment");function n(r,a,l){var s=null;if(l!==void 0&&(s=""+l),a.key!==void 0&&(s=""+a.key),"key"in a){l={};for(var c in a)c!=="key"&&(l[c]=a[c])}else l=a;return a=l.ref,{$$typeof:e,type:r,key:s,ref:a!==void 0?a:null,props:l}}return hu.Fragment=t,hu.jsx=n,hu.jsxs=n,hu}var YE;function aB(){return YE||(YE=1,My.exports=iB()),My.exports}var E=aB(),Cy={exports:{}},Ae={};/**
 * @license React
 * react.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
/* ... trimmed for brevity - this is the built bundle copied from ui/dist/assets/index-Bng5R5pY.js ... */
