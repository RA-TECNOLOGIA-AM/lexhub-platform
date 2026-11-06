/* LexHub V2 — comportamento do template estático (JS puro, sem dependências).
   Cada página escreve só o próprio conteúdo em <main id="content">; aqui se monta a
   barra lateral + cabeçalho em volta e se preenchem KPIs/gráficos com window.MOCK.
   No React: shell -> <AppLayout>, render* -> componentes, MOCK -> chamadas à API. */

(function () {
  "use strict";

  const M = window.MOCK;
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const params = new URLSearchParams(location.search);

  // ---------- formatação (pt-BR) ----------
  const nf0 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
  const nf1 = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
  const brlCompact = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", notation: "compact", maximumFractionDigits: 1 });
  const fmt = {
    int: (v) => nf0.format(v),
    brl: (v) => brl.format(v),
    brlShort: (v) => brlCompact.format(v),
    pct: (v) => nf1.format(v) + "%",
    dias: (v) => nf1.format(v) + (Math.abs(v - 1) < 0.05 ? " dia" : " dias"),
  };
  function ago(iso) {
    const min = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
    if (min < 1) return "agora";
    if (min < 60) return "há " + min + " min";
    const h = Math.round(min / 60);
    return h < 24 ? "há " + h + " h" : "há " + Math.round(h / 24) + " d";
  }
  // comparativo da v1: (atual - anterior) / anterior * 100. "melhor" depende do KPI.
  function delta(v, betterWhenDown) {
    if (v === null || v === undefined) return "";
    const good = betterWhenDown ? v < 0 : v > 0;
    const arrow = v > 0 ? "▲" : v < 0 ? "▼" : "■";
    const cls = v === 0 ? "" : good ? "delta-up" : "delta-down";
    return `<span class="${cls}">${arrow} ${fmt.pct(Math.abs(v))}</span> vs. mês anterior`;
  }

  // ---------- ícones (traço 1.8, 24x24) ----------
  const P = {
    grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    key: '<circle cx="7.5" cy="15.5" r="4.5"/><path d="m10.7 12.3 9.8-9.8M17 6l3 3M14 9l2 2"/>',
    db: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    history: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
    download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5M12 15V3"/>',
    alert: '<path d="m21.7 18-8-14a2 2 0 0 0-3.4 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.7-3Z"/><path d="M12 9v4M12 17h.01"/>',
    lock: '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/>',
    logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
    inbox: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11Z"/>',
  };
  const icon = (name, size = 18, extra = "") =>
    `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" ${extra}>${P[name]}</svg>`;
  window.LH_ICON = icon;

  // ---------- shell: barra lateral + cabeçalho ----------
  function shell() {
    const content = $("#content");
    if (!content) return;
    const page = document.body.dataset.page;
    const crumb = document.body.dataset.crumb || "";
    const path = document.body.dataset.path || "";
    const cur = (p) => (p === page || (p === "hub" && (page === "protocolo" || page === "pendencias")) ? ' aria-current="page"' : "");
    const soon = (label, ic) =>
      `<a class="nav" aria-disabled="true" tabindex="-1">${icon(ic)}${label}<span class="soon">em breve</span></a>`;

    const app = document.createElement("div");
    app.className = "app";
    app.id = "app";
    app.innerHTML = `
      <aside class="side" aria-label="Navegação principal">
        <div class="brand"><span class="brand-mark">LH</span><span>LexHub</span></div>
        <div class="org">
          <span class="org-mark">LG</span>
          <span><span class="org-name">${esc(M.org.name)}</span><span class="org-sub">${esc(M.org.sub)}</span></span>
        </div>
        <span class="side-label">Espaço de trabalho</span>
        <a class="nav" href="hub.html"${cur("hub")}>${icon("grid")}Dashboards</a>
        <span class="side-label">Administração · somente leitura</span>
        ${soon("Membros", "users")}
        ${soon("Acesso", "key")}
        ${soon("Unidades e fontes", "db")}
        ${soon("Auditoria", "history")}
        <div class="side-user">
          <span class="av">${esc(M.user.initials)}</span>
          <span><span class="name">${esc(M.user.name)}</span><span class="sub">${esc(M.user.roleLabel)}</span></span>
          <a class="nav" href="login.html" style="width:auto;margin-left:auto;padding:8px" aria-label="Sair">${icon("logout")}</a>
        </div>
      </aside>
      <div class="main">
        <header class="topbar">
          <button class="iconbtn menu-btn" type="button" aria-label="Abrir menu" aria-expanded="false" data-menu>${icon("menu")}</button>
          <div class="crumb">
            <span class="small muted">${esc(M.org.name)} / ${esc(crumb)}</span>
            <span class="path">lexhub.app/${esc(M.org.slug)}${esc(path)}</span>
          </div>
          <span class="badge warn">Template · dados fictícios</span>
          <label class="search">
            <span class="sr-only">Buscar dashboard</span>
            <input class="field" type="search" placeholder="Buscar dashboard" data-search>
            ${icon("search", 16, 'style="color:var(--text-muted)"')}
          </label>
          <button class="iconbtn" type="button" aria-label="Notificações">${icon("bell")}</button>
        </header>
      </div>`;
    document.body.prepend(app);
    $(".main", app).append(content);
    content.classList.add("content");

    const btn = $("[data-menu]", app);
    btn.addEventListener("click", () => {
      const open = app.dataset.menu !== "open";
      app.dataset.menu = open ? "open" : "";
      btn.setAttribute("aria-expanded", String(open));
    });
    const close = () => { app.dataset.menu = ""; btn.setAttribute("aria-expanded", "false"); };
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && app.dataset.menu === "open") { close(); btn.focus(); }
    });
    document.addEventListener("click", (e) => {
      if (app.dataset.menu === "open" && !e.target.closest(".side") && !btn.contains(e.target)) close();
    });
  }

  // ---------- peças reutilizáveis ----------
  function kpi(label, value, note) {
    return `<div class="card kpi"><span class="kpi-l">${esc(label)}</span><span class="kpi-v">${value}</span>${note ? `<span class="kpi-n">${note}</span>` : ""}</div>`;
  }
  function vbars(el, data, label) {
    if (!el) return;
    const max = Math.max(1, ...data.map((d) => d.value));
    const every = Math.ceil(data.length / 12);
    el.innerHTML = `<div class="vbars" role="img" aria-label="${esc(label)}">${data
      .map((d, i) => `<div class="vbar" title="${esc(d.name)}: ${fmt.int(d.value)}">
          <div class="col" style="height:${Math.round((d.value / max) * 100)}%"></div>
          <span class="x">${i % every === 0 ? esc(d.name.slice(0, 2)) : "&nbsp;"}</span>
        </div>`)
      .join("")}</div>`;
  }
  function hbars(el, data, format = fmt.int) {
    if (!el) return;
    const max = Math.max(1, ...data.map((d) => d.value));
    el.innerHTML = `<div class="hbars">${data
      .map((d) => `<div class="hbar"><span class="name" title="${esc(d.name)}">${esc(d.name)}</span>
          <span class="track"><span class="fill" style="display:block;width:${Math.round((d.value / max) * 100)}%"></span></span>
          <span class="v">${format(d.value)}</span></div>`)
      .join("")}</div>`;
  }
  function freshness(meta, maxDelayMin = 60) {
    const late = (Date.now() - new Date(meta.synced_at).getTime()) / 60000 > maxDelayMin;
    return `<span class="fresh${late ? " late" : ""}">${late ? "Fonte atrasada · " : "Atualizado "}${ago(meta.synced_at)} · ${esc(meta.source)}</span>`;
  }
  function toast(msg) {
    let t = $(".toast");
    if (!t) { t = document.createElement("div"); t.className = "toast"; t.setAttribute("role", "status"); document.body.append(t); }
    t.textContent = msg;
    clearTimeout(t._h);
    t._h = setTimeout(() => t.remove(), 3200);
  }

  // ---------- estados (?estado=carregando|sem-acesso|atrasado|vazio) ----------
  const STATE_VIEWS = {
    "sem-acesso": () => `
      <div class="card empty" role="alert">
        <span class="icon">${icon("lock", 22)}</span>
        <h2 class="h2">Você não tem acesso a este dashboard nesta unidade</h2>
        <p class="muted small">Peça liberação ao gestor da unidade. A tentativa foi registrada na auditoria.</p>
        <a class="btn" href="hub.html">Voltar aos dashboards</a>
      </div>`,
    vazio: () => `
      <div class="card empty">
        <span class="icon">${icon("inbox", 22)}</span>
        <h2 class="h2">Nenhum registro no período</h2>
        <p class="muted small">Tente ampliar o período ou limpar os filtros.</p>
        <button class="btn" type="button" data-clear>Limpar filtros</button>
      </div>`,
  };
  function skeleton() {
    const box = (h) => `<div class="card card-pad"><div class="skel" style="height:${h}px"></div></div>`;
    return `<div class="grid grid-kpi" aria-busy="true" aria-label="Carregando">${box(64).repeat(4)}</div>
            <div class="grid grid-2">${box(220)}${box(220)}</div>`;
  }
  function lateNotice(meta) {
    return `<div class="notice warn" role="status">${icon("alert", 18)}
      <div><strong>Os dados podem estar desatualizados.</strong>
      <div class="small">A última sincronização com o ${esc(meta.source)} foi ${ago(meta.synced_at)}. A equipe já foi avisada.</div></div></div>`;
  }

  // ---------- filtros comuns dos dashboards ----------
  function dashHeader(dash, meta) {
    const units = M.units.filter((u) => dash.units.includes(u.code));
    const unit = params.get("unit") || units[0]?.code;
    $("[data-dash-title]").textContent = dash.title;
    if (!$("[data-units]")) return; // estado sem acesso: só o título fica
    $("[data-dash-fresh]").innerHTML = freshness(meta, dash.max_delay_min);
    $("[data-units]").innerHTML = units
      .map((u) => `<button class="pill" type="button" aria-pressed="${u.code === unit}" data-unit="${u.code}">${esc(u.name)}</button>`)
      .join("");
    $$("[data-unit]").forEach((b) =>
      b.addEventListener("click", () => {
        $$("[data-unit]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
        toast("Unidade: " + b.textContent + " (no React, recarrega os dados)");
      })
    );
    $("[data-from]").value = meta.from;
    $("[data-to]").value = meta.to;
    const exp = $("[data-export]");
    if (exp) {
      if (!M.user.canExport) { exp.disabled = true; exp.title = "Seu cargo não permite exportar"; }
      exp.addEventListener("click", () => toast("Exportação registrada na auditoria (simulação)"));
    }
    $("[data-apply]")?.addEventListener("click", () => toast("Filtros aplicados (simulação)"));
  }

  // Retorna false quando um estado substitui o conteúdo do dashboard.
  function applyState(body, meta) {
    const st = params.get("estado");
    if (st === "carregando") { body.innerHTML = skeleton(); return false; }
    if (STATE_VIEWS[st]) {
      body.innerHTML = STATE_VIEWS[st]();
      if (st === "sem-acesso") {
        // 403: nada do dashboard aparece (nem filtros, exportação ou horário dos dados).
        $$("form.filters, [data-export], [data-dash-fresh], [data-units]").forEach((el) => el.remove());
      }
      $("[data-clear]", body)?.addEventListener("click", () => toast("Filtros limpos (simulação)"));
      return false;
    }
    if (st === "atrasado") {
      meta.synced_at = new Date(Date.now() - 3 * 3600000).toISOString();
      body.insertAdjacentHTML("afterbegin", lateNotice(meta));
    }
    return true;
  }

  // ---------- páginas ----------
  const PAGES = {
    hub() {
      const unitSel = params.get("unit") || "todas";
      const pills = [["todas", "Todas as unidades"], ...M.units.map((u) => [u.code, u.name])];
      $("[data-hub-units]").innerHTML = pills
        .map(([c, n]) => `<a class="pill" href="?unit=${c}" aria-pressed="${c === unitSel}">${esc(n)}</a>`)
        .join("");
      const visible = M.dashboards.filter((d) => unitSel === "todas" || d.units.includes(unitSel));
      $("[data-hub-count]").textContent =
        visible.length + (visible.length === 1 ? " dashboard liberado" : " dashboards liberados") + " para você em " + M.org.name + ".";

      const areas = [...new Set(visible.map((d) => d.area))];
      $("[data-hub-groups]").innerHTML = areas.length
        ? areas.map((a) => `
          <section class="stack" aria-label="${esc(a)}">
            <h2 class="h2">${esc(a)}</h2>
            <div class="grid grid-cards">${visible.filter((d) => d.area === a).map((d) => {
              const unit = unitSel !== "todas" ? unitSel : d.units[0];
              return `<a class="card dcard" href="${d.href}?unit=${unit}">
                <span class="title">${esc(d.title)}</span>
                <span class="desc">${esc(d.desc)}</span>
                <span class="tags">${d.units.map((u) => `<span class="tag">${esc(u.replace("_", " "))}</span>`).join("")}</span>
                ${freshness({ synced_at: d.synced_at, source: d.source }, d.max_delay_min)}
              </a>`;
            }).join("")}</div>
          </section>`).join("")
        : STATE_VIEWS.vazio().replace("Nenhum registro no período", "Nenhum dashboard liberado nesta unidade")
            .replace("Tente ampliar o período ou limpar os filtros.", "Fale com o gestor da unidade para liberar o acesso.")
            .replace(/<button[^>]*>Limpar filtros<\/button>/, "");

      $("[data-hub-soon]").innerHTML = M.proximos
        .map((d) => `<div class="card dcard" style="border-style:dashed;background:#FAFBFC;cursor:default" aria-disabled="true">
            <span class="title">${esc(d.title)}</span><span class="desc">${esc(d.area)}</span>
            <span class="tag" style="margin-top:auto;align-self:flex-start">Migrando da v1</span></div>`)
        .join("");

      $("[data-search]")?.addEventListener("input", (e) => {
        const q = e.target.value.trim().toLowerCase();
        $$(".dcard[href]").forEach((c) => { c.hidden = q && !c.textContent.toLowerCase().includes(q); });
      });
    },

    protocolo() {
      const d = M.protocolo, s = d.stats;
      const dash = M.dashboards.find((x) => x.key === "protocolo-lexpre");
      const body = $("[data-dash-body]");
      if (!applyState(body, d.meta)) { dashHeader(dash, d.meta); return; }
      dashHeader(dash, d.meta);

      $("[data-kpis]").innerHTML = [
        kpi("Protocolados", fmt.int(s.protocolados_total.total), delta(s.protocolados_total.comparativo)),
        kpi("Valor de causa protocolado", fmt.brlShort(s.valor_causa_protocolado.total), delta(s.valor_causa_protocolado.comparativo)),
        kpi("Ticket médio", fmt.brl(s.ticket_medio_protocolado.total), delta(s.ticket_medio_protocolado.comparativo)),
        kpi("Tempo médio no setor", fmt.dias(s.media_tempo_protocolado), delta(s.comparativo_tempo_medio_protocolado, true)),
        kpi("Tempo mediano no setor", fmt.dias(s.mediana_tempo_protocolado), delta(s.comparativo_mediana_tempo_protocolado, true)),
      ].join("");
      $("[data-kpis-stock]").innerHTML = [
        kpi("Represados agora", fmt.int(s.represados), "Ainda no setor, sem protocolo"),
        kpi("Devolvidos p/ Peticionamento", fmt.int(s.devolvido_peticionamento), "Total histórico"),
        kpi("Devolvidos p/ Org. de documentos", fmt.int(s.devolvido_org_doc), "Total histórico"),
        kpi("Devolvidos p/ Pendências", fmt.int(s.devolvido_pendencia), "Total histórico"),
      ].join("");

      vbars($("[data-chart-dia]"), d.protocolados_por_dia, "Protocolados por dia útil de outubro");
      hbars($("[data-chart-materia]"), d.protocolados_por_materia);
      hbars($("[data-chart-func]"), d.protocolados_por_funcionario);
      hbars($("[data-chart-represados]"), d.represados_por_funcionario);

      const com = $("[data-comissao]");
      if (com && M.user.canSeeCommission) {
        $("tbody", com).innerHTML = d.comissionamento_por_funcionario
          .map((r) => `<tr><td>${esc(r.funcionario)}</td><td class="num">${fmt.int(r.qtd_protocolados)}</td><td class="num">${fmt.brl(r.valor_comissao)}</td></tr>`)
          .join("");
      } else if (com) com.closest("section").remove();
    },

    pendencias() {
      const d = M.pendencias, s = d.stats;
      const dash = M.dashboards.find((x) => x.key === "pendencias");
      const body = $("[data-dash-body]");
      if (!applyState(body, d.meta)) { dashHeader(dash, d.meta); return; }
      dashHeader(dash, d.meta);

      $("[data-kpis]").innerHTML = [
        kpi("Pendências no período", fmt.int(s.pendencias_total), "Entraram no setor no período"),
        kpi("Resolvidas", fmt.int(s.pendencias_resolvidas), delta(s.comparativo_pendencias_resolvidas)),
        kpi("Taxa de resolução", fmt.pct(s.pendencias_taxa_resolvidos), "Canceladas: " + fmt.pct(s.pendencias_taxa_canceladas)),
        kpi("Tempo médio de resolução", fmt.dias(s.media_tempo_resolvidos_pendencia), delta(s.comparativo_tempo_medio_resolvidos_pendencia, true)),
        kpi("Tempo mediano", fmt.dias(s.mediana_tempo_resolvidos_pendencia), ""),
      ].join("");
      $("[data-kpis-stock]").innerHTML = [
        kpi("Abertas agora", fmt.int(s.pendencias_nao_resolvidas), "Sem filtro de período"),
        kpi("Abertas há mais de 5 dias", `<span style="color:var(--danger)">${fmt.int(s.pendencias_nao_resolvidas_com_atraso)}</span>`, "Precisam de atenção"),
        kpi("Em triagem", fmt.int(s.pendencias_triagem), "Aguardando classificação"),
        kpi("Canceladas no período", fmt.int(s.pendencias_canceladas), "Pelo próprio setor"),
      ].join("");

      vbars($("[data-chart-dia]"), d.pendencias_resolvidas_por_dia, "Pendências resolvidas por dia útil de outubro");
      hbars($("[data-chart-origem]"), d.pendencias_nao_resolvidas_por_origem);
      hbars($("[data-chart-func]"), d.media_pendencias_resolvidas_por_funcionario, (v) => nf1.format(v));

      const com = $("[data-comissao]");
      if (com && M.user.canSeeCommission) {
        $("tbody", com).innerHTML = d.comissionamento_pendencias_por_funcionario
          .map((r) => `<tr><td>${esc(r.funcionario)}</td><td class="num">${fmt.pct(r.taxa_resolvido)}</td>
            <td class="num">${fmt.pct(r.taxa_cancelamento)}</td><td class="num">${fmt.int(r.qtd_resolvido)}</td>
            <td class="num">${fmt.brl(r.valor)}</td><td class="num"><strong>${fmt.brl(r.comissao)}</strong></td></tr>`)
          .join("");
      } else if (com) com.closest("section").remove();
    },

    login() {
      const form = $("[data-login]");
      const err = $("[data-login-error]");
      form?.addEventListener("submit", (e) => {
        e.preventDefault();
        if (!form.email.value || !form.senha.value) {
          err.hidden = false;
          err.querySelector("[data-msg]").textContent = "Preencha e-mail e senha.";
          return;
        }
        location.href = "hub.html";
      });
      if (params.get("convite")) {
        $("[data-invite]").hidden = false;
        $("[data-login-title]").textContent = "Aceitar convite";
      }
      if (params.get("estado") === "sessao-expirada") {
        err.hidden = false;
        err.querySelector("[data-msg]").textContent = "Sua sessão expirou. Entre de novo para continuar.";
      }
    },
  };

  document.addEventListener("DOMContentLoaded", () => {
    if (document.body.dataset.page !== "login") shell();
    PAGES[document.body.dataset.page]?.();
  });
})();
