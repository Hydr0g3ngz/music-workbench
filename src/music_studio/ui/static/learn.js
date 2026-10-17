"use strict";
(() => {
  let lang = localStorage.getItem("station-language") || "zh";
  function draw() {
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
    document.querySelectorAll("[data-zh]").forEach((el) => {
      el.textContent = el.dataset[lang];
    });
    document.getElementById("learn-language").textContent =
      lang === "zh" ? "English" : "中文";
  }
  document.getElementById("learn-language").onclick = () => {
    lang = lang === "zh" ? "en" : "zh";
    localStorage.setItem("station-language", lang);
    draw();
  };
  document.getElementById("learn-start").onclick = async (e) => {
    const button = e.currentTarget,
      error = document.getElementById("learn-error");
    button.disabled = true;
    error.textContent = "";
    try {
      const response = await fetch("/api/workstation/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: lang === "zh" ? "我的第一段音乐" : "My first musical sketch",
          demo: true,
        }),
      });
      if (!response.ok)
        throw Error(
          lang === "zh"
            ? "示例暂时无法打开，请稍后重试。"
            : "Cannot open the example. Please retry.",
        );
      const project = await response.json();
      location.href = `/station.html?session=${project.id}&start=example`;
    } catch (err) {
      error.textContent = err.message;
      button.disabled = false;
    }
  };
  draw();
})();
