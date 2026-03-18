const editorTab = document.getElementById("editorTab");
const memoryTab = document.getElementById("memoryTab");

const hymnMode = document.getElementById("hymnMode");
const riscvMode = document.getElementById("riscvMode");

const speedSlider = document.getElementById("speedSlider");
const speedValue = document.getElementById("speedValue");

const importBtn = document.getElementById("importBtn");
const exportBtn = document.getElementById("exportBtn");
const assembleBtn = document.getElementById("assembleBtn");
const exportCodeBtn = document.getElementById("exportCodeBtn");

const backBtn = document.getElementById("backBtn");
const playBtn = document.getElementById("playBtn");
const stepBtn = document.getElementById("stepBtn");
const resetBtn = document.getElementById("resetBtn");

const codeInput = document.getElementById("codeInput");
const outputBox = document.getElementById("outputBox");
const resultsBody = document.getElementById("resultsBody");
const registerBody = document.getElementById("registerBody");
const registerFormat = document.getElementById("registerFormat");
const lineNumbers = document.querySelector(".line-numbers");

let currentMode = "HYMN";
let currentStep = -1;
let assembledLines = [];
let runTimer = null;

let registers = [
    { name: "PC", number: 0, value: 0 },
    { name: "IR", number: 1, value: 0 },
    { name: "AC", number: 2, value: 0 }
];

function setOutput(message, isError = false) {
    outputBox.textContent = message;
    outputBox.style.color = isError ? "#c62828" : "#666";
    outputBox.style.fontStyle = "normal";
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function updateSpeedLabel() {
    speedValue.textContent = `${speedSlider.value} ms`;
}

function setActiveTab(tab) {
    editorTab.classList.remove("active");
    memoryTab.classList.remove("active");
    tab.classList.add("active");

    if (tab === editorTab) {
        setOutput("Editor tab selected.");
    } else {
        setOutput("Memory tab selected. Separate memory screen is not built yet.");
    }
}

function setActiveMode(mode) {
    hymnMode.classList.remove("active");
    riscvMode.classList.remove("active");
    mode.classList.add("active");

    currentMode = mode.textContent.trim();
    codeInput.placeholder =
        currentMode === "HYMN"
            ? "Write HYMN code here..."
            : "Write RISC-V code here...";

    setOutput(`${currentMode} mode selected.`);
}

function updateLineNumbers() {
    const lines = codeInput.value.split("\n").length || 1;
    lineNumbers.innerHTML = "";

    for (let i = 1; i <= lines; i++) {
        const span = document.createElement("span");
        span.textContent = i;
        lineNumbers.appendChild(span);
    }
}

function renderRegisters() {
    registerBody.innerHTML = "";

    registers.forEach((reg) => {
        const row = document.createElement("div");
        row.className = "register-row";

        let displayValue = reg.value;

        if (reg.name === "IR" && typeof reg.value === "string") {
            displayValue = reg.value;
        } else {
            if (registerFormat.value === "DECIMAL") {
                displayValue = Number(reg.value);
            } else if (registerFormat.value === "BINARY") {
                displayValue = "0b" + Number(reg.value).toString(2);
            } else {
                displayValue = "0x" + Number(reg.value).toString(16).toUpperCase();
            }
        }

        row.innerHTML = `
            <span>${reg.name}</span>
            <span>${reg.number}</span>
            <span>${displayValue}</span>
        `;

        registerBody.appendChild(row);
    });
}

function getCleanLines() {
    return codeInput.value
        .split("\n")
        .map((line, index) => ({
            raw: line,
            trimmed: line.trim(),
            originalIndex: index
        }))
        .filter((line) => line.trimmed !== "");
}

function renderResults() {
    resultsBody.innerHTML = "";

    assembledLines.forEach((line, index) => {
        const row = document.createElement("div");
        row.className = "results-row";
        row.dataset.index = index;

        const address = `0x${String(index).padStart(4, "0")}`;
        const fakeCode = currentMode === "HYMN"
            ? `H${String(index).padStart(3, "0")}`
            : `R${String(index).padStart(3, "0")}`;

        row.innerHTML = `
            <span>${address}</span>
            <span>${fakeCode}</span>
            <span>${escapeHtml(line.trimmed)}</span>
        `;

        resultsBody.appendChild(row);
    });
}

function clearHighlights() {
    const rows = resultsBody.querySelectorAll(".results-row");
    rows.forEach((row) => row.classList.remove("active-row"));
}

function highlightCurrentRow() {
    clearHighlights();

    if (currentStep < 0 || currentStep >= assembledLines.length) return;

    const row = resultsBody.querySelector(`[data-index="${currentStep}"]`);
    if (row) row.classList.add("active-row");
}

function mockUpdateRegisters() {
    if (currentStep < 0 || currentStep >= assembledLines.length) {
        registers = [
            { name: "PC", number: 0, value: 0 },
            { name: "IR", number: 1, value: 0 },
            { name: "AC", number: 2, value: 0 }
        ];
        renderRegisters();
        return;
    }

    const currentInstruction = assembledLines[currentStep].trimmed;

    registers = [
        { name: "PC", number: 0, value: currentStep },
        { name: "IR", number: 1, value: currentInstruction.toUpperCase().slice(0, 8) },
        { name: "AC", number: 2, value: (currentStep + 1) * 8 }
    ];

    renderRegisters();
}

function assembleCode() {
    stopRun();

    const rawText = codeInput.value.trim();

    if (!rawText) {
        assembledLines = [];
        resultsBody.innerHTML = "";
        currentStep = -1;
        mockUpdateRegisters();
        setOutput("Cannot assemble empty code.", true);
        return false;
    }

    assembledLines = getCleanLines();

    if (assembledLines.length === 0) {
        resultsBody.innerHTML = "";
        currentStep = -1;
        mockUpdateRegisters();
        setOutput("No valid lines found to assemble.", true);
        return false;
    }

    renderResults();
    currentStep = -1;
    clearHighlights();
    mockUpdateRegisters();
    setOutput(`Assembled ${assembledLines.length} line(s) in ${currentMode} mode.`);
    return true;
}

function stepForward() {
    if (assembledLines.length === 0) {
        const ok = assembleCode();
        if (!ok) return;
    }

    if (currentStep >= assembledLines.length - 1) {
        stopRun();
        setOutput("Reached the end of the program.");
        return;
    }

    currentStep += 1;
    highlightCurrentRow();
    mockUpdateRegisters();

    const line = assembledLines[currentStep];
    setOutput(`Step ${currentStep + 1}: ${line.trimmed}`);
}

function stepBackward() {
    stopRun();

    if (assembledLines.length === 0) {
        setOutput("Nothing to go back through.", true);
        return;
    }

    if (currentStep <= 0) {
        currentStep = -1;
        clearHighlights();
        mockUpdateRegisters();
        setOutput("Returned to start.");
        return;
    }

    currentStep -= 1;
    highlightCurrentRow();
    mockUpdateRegisters();

    const line = assembledLines[currentStep];
    setOutput(`Moved back to step ${currentStep + 1}: ${line.trimmed}`);
}

function stopRun() {
    if (runTimer) {
        clearInterval(runTimer);
        runTimer = null;
    }
}

function runProgram() {
    if (assembledLines.length === 0) {
        const ok = assembleCode();
        if (!ok) return;
    }

    stopRun();

    setOutput("Running mock program...");

    runTimer = setInterval(() => {
        if (currentStep >= assembledLines.length - 1) {
            stopRun();
            setOutput("Run complete.");
            return;
        }

        stepForward();
    }, Number(speedSlider.value));
}

function resetAll() {
    stopRun();
    codeInput.value = "";
    assembledLines = [];
    currentStep = -1;
    resultsBody.innerHTML = "";
    updateLineNumbers();
    mockUpdateRegisters();
    setOutput("Editor and results reset.");
}

function exportTextFile(filename, text) {
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();

    URL.revokeObjectURL(url);
}

function importFile() {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".txt,.asm,.s,.js,.ts";

    input.addEventListener("change", (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();

        reader.onload = (e) => {
            codeInput.value = e.target.result;
            updateLineNumbers();
            setOutput(`Imported file: ${file.name}`);
        };

        reader.onerror = () => {
            setOutput("Failed to import file.", true);
        };

        reader.readAsText(file);
    });

    input.click();
}

function exportCode() {
    const text = codeInput.value;

    if (!text.trim()) {
        setOutput("Nothing to export from editor.", true);
        return;
    }

    exportTextFile("assembly-code.txt", text);
    setOutput("Editor code exported.");
}

function exportResults() {
    if (assembledLines.length === 0) {
        setOutput("No assembled results to export.", true);
        return;
    }

    const text = assembledLines
        .map((line, index) => {
            const address = `0x${String(index).padStart(4, "0")}`;
            const fakeCode = currentMode === "HYMN"
                ? `H${String(index).padStart(3, "0")}`
                : `R${String(index).padStart(3, "0")}`;

            return `${address}    ${fakeCode}    ${line.trimmed}`;
        })
        .join("\n");

    exportTextFile("assembly-results.txt", text);
    setOutput("Results exported.");
}

editorTab.addEventListener("click", () => setActiveTab(editorTab));
memoryTab.addEventListener("click", () => setActiveTab(memoryTab));

hymnMode.addEventListener("click", () => setActiveMode(hymnMode));
riscvMode.addEventListener("click", () => setActiveMode(riscvMode));

speedSlider.addEventListener("input", updateSpeedLabel);
codeInput.addEventListener("input", updateLineNumbers);
registerFormat.addEventListener("change", renderRegisters);

importBtn.addEventListener("click", importFile);
exportBtn.addEventListener("click", exportCode);
assembleBtn.addEventListener("click", assembleCode);
exportCodeBtn.addEventListener("click", exportResults);

backBtn.addEventListener("click", stepBackward);
playBtn.addEventListener("click", runProgram);
stepBtn.addEventListener("click", stepForward);
resetBtn.addEventListener("click", resetAll);

updateSpeedLabel();
updateLineNumbers();
renderRegisters();