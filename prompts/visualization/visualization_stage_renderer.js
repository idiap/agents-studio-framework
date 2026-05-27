// SPDX-FileCopyrightText: Copyright © 2025 Idiap Research Institute <contact@idiap.ch>
// SPDX-FileContributor: Imen Ben Mahmoud <imen.benmahmoud@idiap.ch>
//
// SPDX-License-Identifier: GPL-3.0-only

let WALTON_COLORS = {};

function initWaltonColors(waltonSchemes) {
    WALTON_COLORS = {};
    waltonSchemes.forEach(scheme => {
        WALTON_COLORS[scheme.label] = scheme.color;
    });
}
// Color helper
function schemeColor(d) {
    if (d.data.type !== "argument") return "#999";
    return WALTON_COLORS[d.data.scheme] || "#999";
}

// ===========================================
// BUILD DETAILS PANEL HTML
// ===========================================
function buildArgumentDetailsHTML(d) {
    let html = `
        <div style="padding:8px; 
                    font-size:13px; 
                    line-height:1.4; 
                    overflow-y:auto; 
                    max-height:180px;">
    `;

    // Full argument
    html += `<b>Full Argument:</b><br>${d.full}<br><br>`;

    // Critical questions
    if (d.critical_questions?.length) {
        html += `<b>Critical Questions:</b><ul>`;
        d.critical_questions.forEach(q => html += `<li>${q}</li>`);
        html += `</ul>`;
    }

    html += `</div>`;
    return html;
}




// Count schemes for Pro / Con
function computeSchemeStats(treeData) {
    const counts = { pro: {}, con: {} };

    function walk(n) {
        if (n.type === "argument") {
            const side = n.side;
            const sch = n.scheme;
            if (!counts[side][sch]) counts[side][sch] = 0;
            counts[side][sch]++;
        }
        (n.children || []).forEach(walk);
    }

    walk(treeData.side_tree);
    return counts;
}
// LEGEND PANEL (right side)

function renderLegend(treeData) {

    const legendDiv = document.getElementById("legend-content");
    legendDiv.innerHTML = "";

    // Count schemes per side
    const stats = computeSchemeStats(treeData);

    function addSide(title, sideStats, color) {
        const header = document.createElement("h3");
        header.textContent = title;
        header.style.color = color;
        legendDiv.appendChild(header);

        const total = Object.values(sideStats).reduce((a,b)=>a+b, 0);

        const totalP = document.createElement("p");
        totalP.textContent = `Arguments: ${total}`;
        totalP.style.marginTop = "-8px";
        legendDiv.appendChild(totalP);

        for (const [scheme, count] of Object.entries(sideStats)) {
            const row = document.createElement("div");
            row.className = "legend-row";

            const box = document.createElement("div");
            box.className = "legend-color-box";
            box.style.background = (WALTON_COLORS[scheme] || "#999");
            row.appendChild(box);

            const text = document.createElement("span");
            text.textContent = `${scheme}: ${count}`;
            row.appendChild(text);

            legendDiv.appendChild(row);
        }

        legendDiv.appendChild(document.createElement("br"));
    }

    addSide("Pro Side", stats.pro, "#2196F3");
    addSide("Con Side", stats.con, "#FF5722");
}
// MAIN RENDER FUNCTION

function renderTree(treeData) {
    if (treeData.walton_schemes) {
        initWaltonColors(treeData.walton_schemes);
    }
    renderLegend(treeData);
    // Clear
    d3.select("#treeContainer").selectAll("*").remove();

    const width = 1300;
    const height = 800;
    const margin = { top: 40, right: 40, bottom: 40, left: 200 };

    let i = 0;

    // SVG + zoom
    const svg = d3.select("#treeContainer")
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .call(d3.zoom()
            .scaleExtent([0.4, 3])
            .on("zoom", e => g.attr("transform", e.transform)))
        .on("dblclick.zoom", null);

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    // Tree layout
    const treemap = d3.tree().size([
        height - margin.top - margin.bottom,
        width - margin.left - margin.right
    ]);

    const root = d3.hierarchy(treeData.side_tree);

    // collapse all children initially
    root.children?.forEach(collapseAll);

    // keep Pro and Con visible
    root.children?.forEach(child => {
        if (child._children) {
            child.children = child._children;
            child._children = null;
        }
    });

    root.x0 = height / 2;
    root.y0 = 0;

    update(root);
    renderLegend(treeData);
    renderDisagreements(treeData);



    // Collapse helper
    function collapseAll(node) {
        if (node.children) {
            node._children = node.children;
            node._children.forEach(collapseAll);
            node.children = null;
        }
    }

    // ===========================================
    // UPDATE FUNCTION
    // ===========================================
    function update(source) {

        const treeLayout = treemap(root);
        const nodes = treeLayout.descendants();
        const links = treeLayout.links();

        // dynamic horizontal spacing based on text
        nodes.forEach(d => {
            const txt = d.data.summary || d.data.text || "";
            const base = 240;
            const factor = 6;
            const spacing = base + factor * Math.min(txt.length, 35);
            d.y = d.depth * spacing;
        });

        // --------------------
        // NODES
        // --------------------
        const node = g.selectAll("g.node")
            .data(nodes, d => d.id || (d.id = ++i));

        const nodeEnter = node.enter().append("g")
            .attr("class", "node")
            .attr("transform", d => `translate(${source.y0}, ${source.x0})`)
            .on("click", function(event, d) {

    // =======================================
    // 1. ARGUMENT NODE → Toggle details panel
    // =======================================
    if (d.data.type === "argument") {

        const details = d3.select(this).select(".details");
        const visible = details.style("display") !== "none";

        // Toggle argument detail panel
        details.style("display", visible ? "none" : "block")
               .attr("height", visible ? 1 : 200);

        // Expand premises if collapsed
        if (d._children) {
            d.children = d._children;
            d._children = null;
        }

        update(d);
        return;
    }

    // =======================================
    // 2. PREMISE NODE → Collapse ONLY ITSELF
    // =======================================
if (d.data.type === "premise") {

    // Toggle hidden flag
    d.data.hidden = !d.data.hidden;

    // Hide node visually (not structurally)
    const nodeGroup = d3.select(this);
    nodeGroup.style("opacity", d.data.hidden ? 0 : 1)
              .style("pointer-events", d.data.hidden ? "none" : "auto");

    // Hide its incoming link
    g.selectAll("path.link")
        .filter(l => l.target === d)
        .style("opacity", d.data.hidden ? 0 : 1)
        .style("pointer-events", d.data.hidden ? "none" : "auto");

    return; // Do NOT call update()
}


    // =======================================
    // 3. DEFAULT COLLAPSE / EXPAND BEHAVIOR
    // For claims, pro/con sides, issue
    // =======================================
    if (d.children) {
        d._children = d.children;
        d.children = null;
    } else {
        d.children = d._children;
        d._children = null;
    }

    update(d);
});



        // Node circle
        nodeEnter.append("circle")
            .attr("r", 10)
            .attr("fill", d => {
                if (d.data.type === "argument") return schemeColor(d);
                if (d.data.type === "issue") return "#4CAF50";
                if (d.data.side === "pro") return "#2196F3";
                if (d.data.side === "con") return "#FF5722";
                return "#ccc";
            });

        // Short summary label
        // Label text
nodeEnter.append("text")
    .attr("class", "node-label")
    .attr("dy", "-1.2em")
    .attr("text-anchor", "middle")
    .style("font-size", "14px")
    .style("font-weight", d => d.data.type === "argument" ? "bold" : "normal")
    .text(d => d.data.summary || d.data.text);

// ⚠️ Conflict icon for disagreeing premises
nodeEnter.append("text")
    .attr("class", "conflict-icon")
    .attr("dy", "-1.2em")
    .attr("x", 40)   // offset right of label
    .attr("text-anchor", "start")
    .style("font-size", "18px")
    .style("fill", "#e53935")
    .style("display", d =>
        d.data.type === "premise" && d.data.disagrees_with?.length
            ? "block"
            : "none"
    )
    .text("⚠️")
    .append("title")   // tooltip
    .text(d =>
        `This premise disagrees with: ${d.data.disagrees_with?.join(", ")}`
    );


        // EXPANDABLE DETAILS BLOCK
        nodeEnter.append("foreignObject")
    .attr("class", "details")
    .attr("x", -150)
    .attr("y", 20)
    .attr("width", 320)
    .attr("height", 1)
    .style("display", "none")
    .html(d => 
        d.data.type === "argument" 
        ? buildArgumentDetailsHTML(d.data) 
        : ""
    );


        // Transition
        const nodeUpdate = nodeEnter.merge(node);
        nodeUpdate.attr("transform", d => `translate(${d.y}, ${d.x})`);

        node.exit().remove();

        // --------------------
        // LINKS
        // --------------------
        const link = g.selectAll("path.link")
            .data(links, d => d.target.id);

        const linkEnter = link.enter().insert("path", "g")
            .attr("class", "link")
            .attr("stroke", "#333")
            .attr("stroke-width", 2)
            .attr("fill", "none")
            .attr("d", d => diagonal(source, source));

        linkEnter.merge(link)
            .attr("d", d => diagonal(d.source, d.target));

        link.exit().remove();

        // Save old positions
        nodes.forEach(d => {
            d.x0 = d.x;
            d.y0 = d.y;
        });
    }

    function diagonal(s, d) {
        return `
            M ${s.y} ${s.x}
            C ${(s.y + d.y) / 2} ${s.x},
              ${(s.y + d.y) / 2} ${d.x},
              ${d.y} ${d.x}
        `;
    }
}
function renderDisagreements(data) {
    const div = document.getElementById("disagreement-content");

    // For now: placeholder
    div.innerHTML = `
        <p style="color:#777; margin:0;">
            No disagreement analysis included yet.
        </p>
    `;
}

