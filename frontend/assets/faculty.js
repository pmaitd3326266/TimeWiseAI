// Visible, screen-reader-friendly status feedback; no blocking alert dialogs.
const facultyStatus = document.getElementById("facultyStatus");
function notifyFaculty(message, isError = false) {
    facultyStatus.textContent = String(message);
    facultyStatus.classList.toggle("feedback-error", isError);
}

const departmentSelect = document.getElementById("departmentSelect");
    const semesterSelect = document.getElementById("semesterSelect");
    const subjectSelect = document.getElementById("subjectSelect");

    // LOAD SUBJECTS
    async function loadSubjects() {
        const branch = departmentSelect.value;
        const semester = semesterSelect.value;

        if (!branch || !semester) {
            subjectSelect.innerHTML =
                '<option value="">Select branch and semester</option>';
            return;
        }

        subjectSelect.innerHTML =
            '<option value="">Loading subjects...</option>';

        try {
            const response = await fetch(
                `/api/subjects?branch=${encodeURIComponent(branch)}&semester=${semester}`
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Unable to load subjects");
            }

            subjectSelect.innerHTML =
                '<option value="">Select Subject</option>';

            if (data.subjects.length === 0) {
                subjectSelect.innerHTML =
                    '<option value="">No subjects available</option>';
                return;
            }

            data.subjects.forEach(subject => {
                const option = document.createElement("option");
                option.value = subject.code;
                option.textContent = `${subject.code} - ${subject.name}`;
                subjectSelect.appendChild(option);
            });

        } catch (error) {
            subjectSelect.innerHTML =
                '<option value="">Error loading subjects</option>';
            notifyFaculty(error.message || "Unable to load subjects.", true);
            console.error(error);
        }
    }

    departmentSelect.addEventListener("change", loadSubjects);
    semesterSelect.addEventListener("change", loadSubjects);


    // SAVE FACULTY INFORMATION
    const saveFacultyButton =
        document.getElementById("saveFacultyButton");

    saveFacultyButton.addEventListener("click", async function () {

        const facultyData = {
            faculty_name: document.getElementById("facultyName").value.trim(),
            faculty_id: document.getElementById("facultyId").value.trim(),
            branch: departmentSelect.value,
            semester: semesterSelect.value,
            subject: subjectSelect.value,
            weekly_lectures: document.getElementById("weeklyLectures").value
        };

        if (Object.values(facultyData).some(value => value === "")) {
            notifyFaculty("Please fill all faculty information!", true);
            return;
        }

        try {
            const response = await fetch("/api/save-faculty", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                   
                },
                body: JSON.stringify(facultyData)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || "Unable to save information");
            }

            notifyFaculty(result.message);

        } catch (error) {
            notifyFaculty(error.message, true);
            console.error(error);
        }
    });


    // ── Module-level timetable store (for analytics + editing) ──
    let currentTimetableData = null;

    // GENERATE WEEKLY TIMETABLE
    const generateTimetableButton =
        document.getElementById("generateTimetableButton");

    const timetableResult =
        document.getElementById("timetableResult");

    generateTimetableButton.addEventListener("click", async function () {

        const branch = departmentSelect.value;
        const semester = semesterSelect.value;

        if (!branch || !semester) {
            notifyFaculty("Please select branch and semester first!", true);
            return;
        }

        generateTimetableButton.disabled = true;
        generateTimetableButton.textContent = "Generating...";

        try {
            const response = await fetch(
                `/api/generate-timetable?branch=${encodeURIComponent(branch)}&semester=${semester}`,
              
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Timetable generation failed.");
            }

            currentTimetableData = data.timetable;
            renderTimetable(currentTimetableData);
            computeAndShowAnalytics(currentTimetableData);

            notifyFaculty("Weekly timetable generated successfully!");
            timetableResult.focus();

        } catch (error) {
            notifyFaculty(error.message, true);
            console.error(error);

        } finally {
            generateTimetableButton.disabled = false;
            generateTimetableButton.textContent =
                "Generate Weekly Timetable";
        }
    });


    // ── Render timetable with editable cells ──
    function renderTimetable(timetable) {
        timetableResult.innerHTML = "";

        const table = document.createElement("table");
        table.className = "weekly-table";
        const caption = document.createElement("caption");
        caption.textContent = "Generated weekly class timetable. Press Enter on an occupied cell to edit.";
        table.appendChild(caption);

        const header = document.createElement("tr");
        ["Day", "10-11 AM", "11-12 PM", "12-1 PM",
         "2-3 PM", "3-4 PM", "4-5 PM"].forEach(text => {
            const th = document.createElement("th");
            th.textContent = text;
            th.scope = "col";
            header.appendChild(th);
        });
        table.appendChild(header);

        Object.entries(timetable).forEach(([day, lectures]) => {
            const row = document.createElement("tr");

            const dayCell = document.createElement("th");
            dayCell.textContent = day;
            dayCell.scope = "row";
            row.appendChild(dayCell);

            lectures.forEach((lecture, periodIdx) => {
                const td = document.createElement("td");

                if (lecture.subject === "Free") {
                    td.textContent = "FREE";
                    td.className = "free-period";
                } else {
                    const subjSpan = document.createElement("span");
                    subjSpan.textContent = lecture.subject + "\n" + lecture.faculty_name;
                    td.appendChild(subjSpan);

                    const hint = document.createElement("span");
                    hint.className = "cell-edit-hint";
                    hint.textContent = "✏️ double-click or press Enter to edit";
                    td.appendChild(hint);

                    td.className = "editable-cell";
                    td.tabIndex = 0;
                    td.setAttribute("role", "button");
                    td.setAttribute("aria-label", `${day}, period ${periodIdx + 1}, ${lecture.subject}, ${lecture.faculty_name}. Press Enter to edit.`);
                    td.onkeydown = function (event) {
                        if (event.target !== td) return;
                        if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            openCellEditor(td, day, periodIdx, lecture);
                        }
                    };
                    td.dataset.day = day;
                    td.dataset.period = periodIdx;

                    td.ondblclick = function () {
                        openCellEditor(td, day, periodIdx, lecture);
                    };
                }

                row.appendChild(td);
            });

            table.appendChild(row);
        });

        timetableResult.appendChild(table);
    }


    // ── Compute workload analytics and conflict detection ──
    function computeAndShowAnalytics(timetable) {
        const allLectures = Object.values(timetable).flat();
        const scheduled = allLectures.filter(l => l.subject !== "Free");
        const free      = allLectures.filter(l => l.subject === "Free");

        document.getElementById("statScheduled").textContent = scheduled.length;
        document.getElementById("statHours").textContent    = scheduled.length + "h";
        document.getElementById("statFree").textContent     = free.length;

        // ── Subject-wise lecture distribution ──
        const subjectCount = {};
        scheduled.forEach(l => {
            subjectCount[l.subject] = (subjectCount[l.subject] || 0) + 1;
        });

        const distContainer = document.getElementById("subjectDistribution");
        distContainer.innerHTML = "";

        if (Object.keys(subjectCount).length > 0) {
            const heading = document.createElement("h5");
            heading.textContent = "Subject-wise Lecture Distribution";
            heading.style.cssText = "color:#172554; margin-bottom:8px; font-size:14px;";
            distContainer.appendChild(heading);

            Object.entries(subjectCount)
                .sort((a, b) => b[1] - a[1])
                .forEach(([subj, count]) => {
                    const item = document.createElement("div");
                    item.className = "subj-dist-item";

                    const nameSpan = document.createElement("span");
                    nameSpan.textContent = subj;

                    const countSpan = document.createElement("span");
                    countSpan.className = "subj-dist-count";
                    countSpan.textContent = count + (count === 1 ? " lecture" : " lectures");

                    item.appendChild(nameSpan);
                    item.appendChild(countSpan);
                    distContainer.appendChild(item);
                });
        }

        // ── Conflict detection ──
        // Map: "day|period" → list of faculty_id values
        const slotFacultyMap = {};
        const conflicts = [];

        Object.entries(timetable).forEach(([day, lectures]) => {
            lectures.forEach((lecture, pIdx) => {
                if (lecture.subject === "Free" || !lecture.faculty_id) return;
                const key = day + "|" + pIdx;
                if (!slotFacultyMap[key]) slotFacultyMap[key] = [];
                if (slotFacultyMap[key].includes(lecture.faculty_id)) {
                    conflicts.push(
                        `${lecture.faculty_name} (ID: ${lecture.faculty_id}) ` +
                        `is double-booked on ${day}, Period ${pIdx + 1}`
                    );
                }
                slotFacultyMap[key].push(lecture.faculty_id);
            });
        });

        const conflictBanner = document.getElementById("conflictBanner");
        conflictBanner.innerHTML = "";

        if (conflicts.length > 0) {
            const banner = document.createElement("div");
            banner.className = "conflict-banner";

            const title = document.createElement("strong");
            title.textContent = "⚠️ Scheduling Conflicts Detected:";
            banner.appendChild(title);

            const ul = document.createElement("ul");
            ul.style.cssText = "margin-top:6px; padding-left:18px;";
            conflicts.forEach(msg => {
                const li = document.createElement("li");
                li.textContent = msg;
                ul.appendChild(li);
            });
            banner.appendChild(ul);
            conflictBanner.appendChild(banner);

            // Highlight conflicted cells in the rendered table
            highlightConflictedCells(timetable);
        } else if (scheduled.length > 0) {
            const ok = document.createElement("div");
            ok.className = "conflict-ok-banner";
            ok.textContent = "✅ No scheduling conflicts detected. All faculty assignments are valid.";
            conflictBanner.appendChild(ok);
        }

        document.getElementById("workloadAnalytics").style.display = "block";
    }


    // ── Highlight conflicted cells in the rendered table ──
    function highlightConflictedCells(timetable) {
        const slotFacultyMap = {};
        const conflictedKeys = new Set();

        Object.entries(timetable).forEach(([day, lectures]) => {
            lectures.forEach((lecture, pIdx) => {
                if (lecture.subject === "Free" || !lecture.faculty_id) return;
                const key = day + "|" + pIdx;
                if (!slotFacultyMap[key]) slotFacultyMap[key] = [];
                if (slotFacultyMap[key].includes(lecture.faculty_id)) {
                    conflictedKeys.add(key);
                }
                slotFacultyMap[key].push(lecture.faculty_id);
            });
        });

        if (conflictedKeys.size === 0) return;

        // Scan rendered table cells
        const tds = timetableResult.querySelectorAll("td.editable-cell");
        tds.forEach(td => {
            const key = td.dataset.day + "|" + td.dataset.period;
            if (conflictedKeys.has(key)) {
                td.classList.add("conflict-cell");
            }
        });
    }


    // ── Inline cell editor ──
    function openCellEditor(td, day, periodIdx, lecture) {
        // Capture original display text from first child span (or td directly)
        const originalSubj = lecture.subject;
        const originalFac  = lecture.faculty_name;

        // Clear cell, build edit form
        td.innerHTML = "";

        const form = document.createElement("div");
        form.className = "cell-edit-form";

        const subjLabel = document.createElement("label");
        const subjInput = document.createElement("input");
        subjLabel.textContent = "Subject code";
        subjInput.id = `edit-subject-${day.replace(/\W/g, "-")}-${periodIdx}`;
        subjLabel.htmlFor = subjInput.id;
        subjInput.maxLength = 120;
        subjInput.type        = "text";
        subjInput.value       = originalSubj;
        subjInput.placeholder = "Subject code";

        const facLabel = document.createElement("label");
        const facInput = document.createElement("input");
        facLabel.textContent = "Faculty name";
        facInput.id = `edit-faculty-${day.replace(/\W/g, "-")}-${periodIdx}`;
        facLabel.htmlFor = facInput.id;
        facInput.maxLength = 120;
        facInput.type        = "text";
        facInput.value       = originalFac;
        facInput.placeholder = "Faculty name";

        const actions = document.createElement("div");
        actions.className = "cell-edit-actions";

        const saveBtn = document.createElement("button");
        saveBtn.textContent = "Save";
        saveBtn.className   = "btn-cell-save";

        const cancelBtn = document.createElement("button");
        cancelBtn.textContent = "Cancel";
        cancelBtn.className   = "btn-cell-cancel";

        actions.appendChild(saveBtn);
        actions.appendChild(cancelBtn);

        form.appendChild(subjLabel);
        form.appendChild(subjInput);
        form.appendChild(facLabel);
        form.appendChild(facInput);
        form.appendChild(actions);
        td.appendChild(form);
        // Escape cancels editing; editor returns focus to its timetable cell.
        form.addEventListener("keydown", function (event) {
            if (event.key === "Escape") {
                event.stopPropagation();
                rebuildCellContent(td, day, periodIdx, lecture);
                td.focus();
            }
        });
        subjInput.focus();

        // ── Save handler ──
        saveBtn.addEventListener("click", function () {
            const newSubj = subjInput.value.trim() || originalSubj;
            const newFac  = facInput.value.trim()  || originalFac;

            // Update in-memory data
            if (currentTimetableData &&
                currentTimetableData[day] &&
                currentTimetableData[day][periodIdx]) {
                currentTimetableData[day][periodIdx].subject      = newSubj;
                currentTimetableData[day][periodIdx].faculty_name = newFac;
            }

            // Rebuild cell content
            rebuildCellContent(td, day, periodIdx, {
                subject: newSubj,
                faculty_name: newFac,
                faculty_id: lecture.faculty_id
            });

            // Recompute analytics (manual edit may introduce/resolve conflicts)
            computeAndShowAnalytics(currentTimetableData);
            td.focus();
        });

        // ── Cancel handler ──
        cancelBtn.addEventListener("click", function () {
            rebuildCellContent(td, day, periodIdx, lecture);
            td.focus();
        });
    }


    // ── Restore / build a non-free cell after editing ──
    function rebuildCellContent(td, day, periodIdx, lecture) {
        td.innerHTML   = "";
        td.className   = "editable-cell";
        td.tabIndex = 0;
        td.setAttribute("role", "button");
        td.setAttribute("aria-label", `${day}, period ${periodIdx + 1}, ${lecture.subject}, ${lecture.faculty_name}. Press Enter to edit.`);
        td.dataset.day    = day;
        td.dataset.period = periodIdx;

        const subjSpan = document.createElement("span");
        subjSpan.textContent = lecture.subject + "\n" + lecture.faculty_name;
        td.appendChild(subjSpan);

        const hint = document.createElement("span");
        hint.className   = "cell-edit-hint";
        hint.textContent = "✏️ double-click or press Enter to edit";
        td.appendChild(hint);

        td.ondblclick = function () {
            openCellEditor(td, day, periodIdx, lecture);
        };
        td.onkeydown = function (event) {
            if (event.target !== td) return;
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                openCellEditor(td, day, periodIdx, lecture);
            }
        };
    }


    // DOWNLOAD PDF
    const downloadPDFButton =
        document.getElementById("downloadPDFButton");

    downloadPDFButton.addEventListener("click", function () {

        if (timetableResult.innerHTML.trim() === "") {
            notifyFaculty("Please generate the timetable first!", true);
            return;
        }

        window.print();
    });
