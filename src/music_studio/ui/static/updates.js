(() => {
  let language =
    localStorage.getItem("station-language") === "en" ? "en" : "zh";
  function render() {
    document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
    document
      .querySelectorAll("[data-zh]")
      .forEach((el) => (el.textContent = el.dataset[language]));
    document.getElementById("language").textContent =
      language === "zh" ? "EN" : "中文";
  }
  document.getElementById("language").onclick = () => {
    language = language === "zh" ? "en" : "zh";
    localStorage.setItem("station-language", language);
    render();
  };
  render();
  fetch("/api/workstation/instance")
    .then((r) => {
      if (!r.ok) throw Error(r.status);
      return r.json();
    })
    .then(
      (info) => (document.getElementById("version").textContent = info.version),
    )
    .catch(
      () =>
        (document.getElementById("version").textContent =
          "暂时无法读取 / Unavailable"),
    );
})();
