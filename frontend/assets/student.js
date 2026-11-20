// Accessible, non-blocking status feedback.
const studentFeedback = document.getElementById("studentFeedback");
function notifyStudent(message) {
    studentFeedback.textContent = String(message);
    studentFeedback.classList.toggle("feedback-error", /please|error|failed|unable|invalid/i.test(String(message)));
}

let subjects = [];

const subjectInput = document.getElementById("subjectInput");
const addSubjectButton = document.getElementById("addSubjectButton");
const subjectList = document.getElementById("subjectList");

addSubjectButton.addEventListener("click", function () {
    const subject = subjectInput.value.trim();

    if (subject === "") {
        notifyStudent("Please enter a subject name!");
        return;
    }

    if (subjects.includes(subject)) {
        notifyStudent("This subject is already added!");
        return;
    }

    subjects.push(subject);
    subjectInput.value = "";

    displaySubjects();
});

function displaySubjects() {
    subjectList.innerHTML = "";

    subjects.forEach(function (subject, index) {
        const item = document.createElement("div");

        item.style.display = "flex";
        item.style.justifyContent = "space-between";
        item.style.alignItems = "center";
        item.style.padding = "10px";
        item.style.marginBottom = "8px";
        item.style.background = "#f1f5f9";
        item.style.borderRadius = "8px";

        const name = document.createElement("span");
        name.textContent = subject;

        const removeButton = document.createElement("button");
        removeButton.textContent = "Remove";
        removeButton.style.background = "#dc2626";

        removeButton.addEventListener("click", function () {
            subjects.splice(index, 1);
            displaySubjects();
        });

        item.appendChild(name);
        item.appendChild(removeButton);

        subjectList.appendChild(item);
    });

    if (typeof updatePerformanceAnalytics === "function") {
        updatePerformanceAnalytics();
    }
}


document.getElementById("generateStudyPlanButton")
.addEventListener("click", function () {

    const name = document.getElementById("studentName").value.trim();
    const branch = document.getElementById("studentBranch").value;
    const semester = document.getElementById("studentSemester").value;
    const studyHours = Number(document.getElementById("studyHours").value);
    const examDate = document.getElementById("examDate").value;

    if (!name || !branch || !semester || !studyHours || !examDate) {
        notifyStudent("Please fill all student details and study preferences!");
        return;
    }

    if (subjects.length === 0) {
        notifyStudent("Please add at least one subject!");
        return;
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const exam = new Date(examDate + "T00:00:00");

    if (isNaN(exam.getTime()) || exam < today) {
        notifyStudent("Please select a valid future exam date!");
        return;
    }
document.getElementById("generateStudyPlanButton")
    const remainingDays = Math.ceil(
        (exam - today) / (1000 * 60 * 60 * 24)
    );

    // Get only pending topics
    const pendingTopics = studyTopics.filter(function(item) {
        return !item.completed;
    });

    // Count pending topics for each subject
    const subjectPriority = {};

    subjects.forEach(function(subject) {
        subjectPriority[subject] = pendingTopics.filter(function(item) {
            return item.subject === subject;
        }).length;
    });

    // Subjects with more pending topics get higher priority
    pendingTopics.sort(function(a, b) {
        return subjectPriority[b.subject] - subjectPriority[a.subject];
    });

    const result = document.getElementById("studyPlanResult");
    result.innerHTML = "";

    const heading = document.createElement("h2");
    heading.textContent = "🧠 Your Smart AI Study Plan";
    result.appendChild(heading);

    const details = document.createElement("p");
    details.textContent =
        name + " | " + branch + " | Semester " + semester;
    result.appendChild(details);

    const countdown = document.createElement("h3");
    countdown.textContent =
        "⏳ " + remainingDays + " days remaining until your exam!";
    countdown.style.color = "#7c3aed";
    result.appendChild(countdown);

    const summary = document.createElement("p");
    summary.textContent =
        "📚 Daily Study: " + studyHours + " hours | " +
        "Pending Topics: " + pendingTopics.length +
        " | Completed Topics: " +
        studyTopics.filter(function(item) {
            return item.completed;
        }).length;

    result.appendChild(summary);

    const days = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday"
    ];

    let topicIndex = 0;

    // Track subject-wise study sessions
const sessionDistribution = {};

subjects.forEach(function(subject) {
    sessionDistribution[subject] = 0;
});
    days.forEach(function(day) {

        const dayCard = document.createElement("div");

        dayCard.style.background = "#f1f5f9";
        dayCard.style.padding = "15px";
        dayCard.style.marginTop = "15px";
        dayCard.style.borderRadius = "10px";

        const dayHeading = document.createElement("h3");
        dayHeading.textContent = "📅 " + day;
        dayCard.appendChild(dayHeading);

        for (let hour = 0; hour < studyHours; hour++) {

            const session = document.createElement("p");

            if (topicIndex < pendingTopics.length) {

                const topic = pendingTopics[topicIndex];

                session.textContent =
                    "📖 Session " + (hour + 1) + ": " +
                    topic.subject + " — " + topic.topic;
                sessionDistribution[topic.subject]++;
                topicIndex++;

            } else {

                const revisionSubject =
                    subjects[(hour + days.indexOf(day)) % subjects.length];

                session.textContent =
                    "🔄 Session " + (hour + 1) +
                    ": Revision and Practice — " + revisionSubject;
            }

            dayCard.appendChild(session);
        }

        result.appendChild(dayCard);
    });

    const note = document.createElement("p");
    note.textContent =
        "💡 Tip: Complete your pending topics first, then use revision sessions for practice and exam preparation.";

    note.style.marginTop = "20px";
    note.style.fontWeight = "bold";

    result.appendChild(note);

// Subject-wise Study Distribution

const distributionHeading = document.createElement("h3");
distributionHeading.textContent = "📊 Subject-wise Study Distribution";
distributionHeading.style.marginTop = "25px";

result.appendChild(distributionHeading);

subjects.forEach(function(subject) {

    const subjectRow = document.createElement("p");

    subjectRow.textContent =
        "📚 " + subject + " — " +
        sessionDistribution[subject] + " study sessions";

    result.appendChild(subjectRow);
});


    result.scrollIntoView({ behavior: "smooth" });

});


// ==========================================
// Gemini AI Adaptive Study Planner
// ==========================================

const optimizeWithGeminiButton = document.getElementById("optimizeWithGeminiButton");

function formatAdaptiveDate(dateStr) {
    if (!dateStr) return "";
    try {
        const parts = dateStr.split("-");
        if (parts.length === 3) {
            const d = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
            if (!isNaN(d.getTime())) {
                const options = { weekday: 'long', year: 'numeric', month: 'short', day: 'numeric' };
                return d.toLocaleDateString(undefined, options);
            }
        }
    } catch (e) {}
    return dateStr;
}

async function generateAdaptivePlanWithGemini() {
    const name = document.getElementById("studentName").value.trim();
    const branch = document.getElementById("studentBranch").value;
    const semester = document.getElementById("studentSemester").value;
    const studyHours = Number(document.getElementById("studyHours").value);
    const examDate = document.getElementById("examDate").value;

    if (!name || !branch || !semester || !studyHours || !examDate) {
        notifyStudent("Please fill your student details, study hours, and upcoming exam date first!");
        return;
    }

    if (subjects.length === 0) {
        notifyStudent("Please add at least one subject!");
        return;
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const exam = new Date(examDate + "T00:00:00");

    if (isNaN(exam.getTime()) || exam < today) {
        notifyStudent("Please select a valid future exam date!");
        return;
    }

    const remainingDays = Math.ceil((exam - today) / (1000 * 60 * 60 * 24));

    const pendingTopics = studyTopics.filter(function (item) {
        return !item.completed;
    });

    const completedTopics = studyTopics.filter(function (item) {
        return item.completed;
    });

    const result = document.getElementById("studyPlanResult");
    result.innerHTML = "";

    // Show loading state
    const loadingCard = document.createElement("div");
    loadingCard.style.padding = "30px";
    loadingCard.style.textAlign = "center";
    loadingCard.style.background = "#f8fafc";
    loadingCard.style.border = "1px solid #e2e8f0";
    loadingCard.style.borderRadius = "12px";

    const loadingEmoji = document.createElement("div");
    loadingEmoji.textContent = "✨";
    loadingEmoji.style.fontSize = "32px";
    loadingEmoji.style.marginBottom = "10px";
    loadingCard.appendChild(loadingEmoji);

    const loadingTitle = document.createElement("h3");
    loadingTitle.textContent = "Gemini is building your adaptive study plan...";
    loadingTitle.style.color = "#172554";
    loadingTitle.style.marginBottom = "8px";
    loadingCard.appendChild(loadingTitle);

    const loadingSubtitle = document.createElement("p");
    loadingSubtitle.textContent = "Balancing your pending topics, daily study hours, and exam deadline with spaced repetition.";
    loadingSubtitle.style.color = "#64748b";
    loadingSubtitle.style.fontSize = "14px";
    loadingCard.appendChild(loadingSubtitle);

    result.appendChild(loadingCard);
    result.scrollIntoView({ behavior: "smooth" });

    optimizeWithGeminiButton.disabled = true;
    optimizeWithGeminiButton.textContent = "✨ Optimizing with Gemini...";

    const payload = {
        branch: branch,
        semester: semester,
        subjects: subjects,
        pendingTopics: pendingTopics,
        completedTopics: completedTopics,
        examDate: examDate,
        availableHours: studyHours,
        currentDate: new Date().toISOString().split("T")[0]
    };

    try {
        const response = await fetch("/api/ai/adaptive-plan", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json().catch(function () { return {}; });

        if (!response.ok || !data.plan) {
            const errorMsg = data.error || ("Server error (" + response.status + "): Unable to generate plan.");
            renderAdaptiveError(errorMsg);
            return;
        }

        renderAdaptivePlan(data, name, branch, semester, studyHours, remainingDays, pendingTopics.length, completedTopics.length);

    } catch (networkError) {
        renderAdaptiveError("Network error: Unable to communicate with the AI planner. Please check your connection and ensure the Flask server is running.");
    } finally {
        optimizeWithGeminiButton.disabled = false;
        optimizeWithGeminiButton.textContent = "✨ Optimize with Gemini";
    }
}

function renderAdaptiveError(errorMessage) {
    const result = document.getElementById("studyPlanResult");
    result.innerHTML = "";

    const errBox = document.createElement("div");
    errBox.style.padding = "22px";
    errBox.style.background = "#fef2f2";
    errBox.style.border = "1px solid #fecaca";
    errBox.style.borderRadius = "12px";
    errBox.style.color = "#991b1b";

    const heading = document.createElement("h3");
    heading.textContent = "⚠️ Unable to Generate Adaptive Plan";
    errBox.appendChild(heading);

    const desc = document.createElement("p");
    desc.textContent = errorMessage;
    desc.style.marginTop = "8px";
    desc.style.fontSize = "14px";
    desc.style.lineHeight = "1.5";
    errBox.appendChild(desc);

    const retryBtn = document.createElement("button");
    retryBtn.type = "button";
    retryBtn.textContent = "🔄 Retry Optimization";
    retryBtn.style.marginTop = "16px";
    retryBtn.style.background = "#dc2626";
    retryBtn.style.color = "white";
    retryBtn.style.padding = "10px 18px";
    retryBtn.style.border = "none";
    retryBtn.style.borderRadius = "8px";
    retryBtn.style.cursor = "pointer";
    retryBtn.addEventListener("click", function () {
        generateAdaptivePlanWithGemini();
    });
    errBox.appendChild(retryBtn);

    result.appendChild(errBox);
    result.scrollIntoView({ behavior: "smooth" });
}

function renderAdaptivePlan(data, name, branch, semester, studyHours, remainingDays, pendingCount, completedCount) {
    const result = document.getElementById("studyPlanResult");
    result.innerHTML = "";

    // Main Heading
    const heading = document.createElement("h2");
    heading.textContent = "🧠 Gemini AI Adaptive Study Plan ✨";
    result.appendChild(heading);

    // Student Details
    const details = document.createElement("p");
    details.textContent = name + " | " + branch + " | Semester " + semester;
    result.appendChild(details);

    // Countdown Badge
    const countdown = document.createElement("h3");
    countdown.textContent = "⏳ " + remainingDays + " days remaining until your exam!";
    countdown.style.color = "#7c3aed";
    countdown.style.marginTop = "6px";
    result.appendChild(countdown);

    // Summary description
    const summary = document.createElement("p");
    summary.textContent = "📚 Target Study: " + studyHours + " hrs/day | ⏳ Pending Topics: " + pendingCount + " | ✅ Completed Topics: " + completedCount;
    summary.style.marginTop = "4px";
    result.appendChild(summary);

    // Days grid / list
    data.plan.forEach(function (day) {
        const dayCard = document.createElement("div");
        dayCard.style.background = "#f1f5f9";
        dayCard.style.padding = "16px 18px";
        dayCard.style.marginTop = "16px";
        dayCard.style.borderRadius = "10px";

        // Calculate total day duration
        const totalMinutes = (day.sessions || []).reduce(function (acc, s) {
            return acc + (Number(s.durationMinutes) || 60);
        }, 0);
        const totalHours = Math.round((totalMinutes / 60) * 10) / 10;

        const dayHeader = document.createElement("div");
        dayHeader.style.display = "flex";
        dayHeader.style.justifyContent = "space-between";
        dayHeader.style.alignItems = "center";
        dayHeader.style.flexWrap = "wrap";
        dayHeader.style.gap = "8px";
        dayHeader.style.marginBottom = "12px";

        const dayTitle = document.createElement("h3");
        dayTitle.textContent = "📅 " + formatAdaptiveDate(day.date);
        dayTitle.style.color = "#172554";
        dayHeader.appendChild(dayTitle);

        const durationBadge = document.createElement("span");
        durationBadge.textContent = "⏱️ " + totalHours + " hrs (" + totalMinutes + "m)";
        durationBadge.style.fontSize = "12px";
        durationBadge.style.fontWeight = "bold";
        durationBadge.style.background = "#e2e8f0";
        durationBadge.style.padding = "4px 10px";
        durationBadge.style.borderRadius = "12px";
        durationBadge.style.color = "#475569";
        dayHeader.appendChild(durationBadge);

        dayCard.appendChild(dayHeader);

        // Sessions list
        (day.sessions || []).forEach(function (session, sIdx) {
            const sessionRow = document.createElement("div");
            sessionRow.style.display = "flex";
            sessionRow.style.alignItems = "center";
            sessionRow.style.padding = "9px 12px";
            sessionRow.style.marginBottom = "8px";
            sessionRow.style.background = "white";
            sessionRow.style.borderRadius = "8px";
            sessionRow.style.border = "1px solid #e2e8f0";

            const badge = document.createElement("span");
            badge.className = "adaptive-session-badge";
            const activity = (session.activity || "Learn").toLowerCase();
            if (activity.includes("revision")) {
                badge.classList.add("badge-revision");
                badge.textContent = "Revision";
            } else if (activity.includes("practice")) {
                badge.classList.add("badge-practice");
                badge.textContent = "Practice";
            } else {
                badge.classList.add("badge-learn");
                badge.textContent = "Learn";
            }
            sessionRow.appendChild(badge);

            const sessionInfo = document.createElement("span");
            sessionInfo.style.flex = "1";
            sessionInfo.style.fontSize = "14px";
            sessionInfo.textContent = (session.subject ? (session.subject + " — ") : "") + session.topic;
            sessionRow.appendChild(sessionInfo);

            const timeSpan = document.createElement("span");
            timeSpan.style.fontSize = "12px";
            timeSpan.style.color = "#64748b";
            timeSpan.textContent = session.durationMinutes + " min";
            sessionRow.appendChild(timeSpan);

            dayCard.appendChild(sessionRow);
        });

        result.appendChild(dayCard);
    });

    // Notes & Study Recommendations
    if (Array.isArray(data.notes) && data.notes.length > 0) {
        const notesCard = document.createElement("div");
        notesCard.style.marginTop = "22px";
        notesCard.style.padding = "16px 20px";
        notesCard.style.background = "#eff6ff";
        notesCard.style.border = "1px solid #bfdbfe";
        notesCard.style.borderRadius = "10px";

        const notesHeading = document.createElement("h3");
        notesHeading.textContent = "💡 Gemini Mentor Recommendations";
        notesHeading.style.color = "#1e40af";
        notesHeading.style.marginBottom = "10px";
        notesCard.appendChild(notesHeading);

        const notesList = document.createElement("ul");
        notesList.style.paddingLeft = "20px";
        notesList.style.color = "#1e3a8a";
        notesList.style.lineHeight = "1.6";
        notesList.style.fontSize = "14px";

        data.notes.forEach(function (note) {
            const li = document.createElement("li");
            li.textContent = note;
            notesList.appendChild(li);
        });

        notesCard.appendChild(notesList);
        result.appendChild(notesCard);
    }

    result.scrollIntoView({ behavior: "smooth" });
}

optimizeWithGeminiButton.addEventListener("click", generateAdaptivePlanWithGemini);



document.getElementById("downloadStudyPlanPDF")
.addEventListener("click", function () {

    const result = document.getElementById("studyPlanResult");

    if (result.innerHTML.trim() === "") {
        notifyStudent("Please generate your study plan first!");
        return;
    }

    window.print();
});

// Study Progress Tracker

let studyTopics = [];

const progressSubject = document.getElementById("progressSubject");
const topicInput = document.getElementById("topicInput");
const addTopicButton = document.getElementById("addTopicButton");
const progressTopicList = document.getElementById("progressTopicList");

// Update subject dropdown
function updateProgressSubjects() {
    const selectedValue = progressSubject.value;

    progressSubject.innerHTML =
        '<option value="">Select Subject</option>';

    subjects.forEach(function(subject) {
        const option = document.createElement("option");
        option.value = subject;
        option.textContent = subject;
        progressSubject.appendChild(option);
    });

    if (subjects.includes(selectedValue)) {
        progressSubject.value = selectedValue;
    }
}

// Update dropdown whenever a subject is added
addSubjectButton.addEventListener("click", function() {
    updateProgressSubjects();
});

// Add a new topic
addTopicButton.addEventListener("click", function() {

    const subject = progressSubject.value;
    const topic = topicInput.value.trim();

    if (!subject) {
        notifyStudent("Please select a subject!");
        return;
    }

    if (!topic) {
        notifyStudent("Please enter a topic name!");
        return;
    }

    const alreadyExists = studyTopics.some(function(item) {
        return item.subject === subject &&
               item.topic.toLowerCase() === topic.toLowerCase();
    });

    if (alreadyExists) {
        notifyStudent("This topic already exists!");
        return;
    }

    studyTopics.push({
        subject: subject,
        topic: topic,
        completed: false
    });

    topicInput.value = "";

    displayProgressTopics();
});

// Display topics
function displayProgressTopics() {

    progressTopicList.innerHTML = "";

    if (studyTopics.length === 0) {
        progressTopicList.textContent = "No topics added yet.";
    }

    studyTopics.forEach(function(item, index) {

        const row = document.createElement("div");

        row.style.display = "flex";
        row.style.justifyContent = "space-between";
        row.style.alignItems = "center";
        row.style.padding = "12px";
        row.style.marginBottom = "10px";
        row.style.background = "#f1f5f9";
        row.style.borderRadius = "8px";

        const topicName = document.createElement("span");

        topicName.textContent =
            item.subject + " — " + item.topic;

        if (item.completed) {
            topicName.style.textDecoration = "line-through";
            topicName.style.color = "#16a34a";
        }

        const completeButton = document.createElement("button");

        completeButton.textContent =
            item.completed ? "Completed ✓" : "Mark Complete";

        completeButton.style.background =
            item.completed ? "#64748b" : "#16a34a";

        completeButton.addEventListener("click", function() {
            studyTopics[index].completed =
                !studyTopics[index].completed;

            displayProgressTopics();
        });

        row.appendChild(topicName);
        row.appendChild(completeButton);

        progressTopicList.appendChild(row);
    });

    updateOverallProgress();
}

// Calculate overall progress
function updateOverallProgress() {

    const total = studyTopics.length;

    const completed = studyTopics.filter(function(item) {
        return item.completed;
    }).length;

    const percentage = total === 0
        ? 0
        : Math.round((completed / total) * 100);

    document.getElementById("overallProgress").textContent =
        percentage + "%";

    document.getElementById("progressBar").style.width =
        percentage + "%";

    // Update Student Performance Analytics dashboard
    updatePerformanceAnalytics();
}

// ==========================================
// Student Performance Analytics Logic
// ==========================================

function updatePerformanceAnalytics() {
    const totalElem = document.getElementById("analyticsTotalTopics");
    const completedElem = document.getElementById("analyticsCompletedTopics");
    const pendingElem = document.getElementById("analyticsPendingTopics");
    const overallPctElem = document.getElementById("analyticsOverallPct");
    const barLabelElem = document.getElementById("analyticsBarLabel");
    const progressBarElem = document.getElementById("analyticsProgressBar");
    const subjectListElem = document.getElementById("analyticsSubjectList");
    const insightsContainerElem = document.getElementById("analyticsInsightsContainer");

    if (!totalElem || !subjectListElem || !insightsContainerElem) {
        return;
    }

    const topics = (typeof studyTopics !== "undefined" && Array.isArray(studyTopics)) ? studyTopics : [];
    const subs = (typeof subjects !== "undefined" && Array.isArray(subjects)) ? subjects : [];

    // 1. Overall Progress Counts
    const totalTopics = topics.length;
    const completedTopics = topics.filter(function (t) { return t.completed; }).length;
    const pendingTopics = totalTopics - completedTopics;
    const overallPct = totalTopics === 0 ? 0 : Math.round((completedTopics / totalTopics) * 100);

    totalElem.textContent = totalTopics;
    completedElem.textContent = completedTopics;
    pendingElem.textContent = pendingTopics;
    overallPctElem.textContent = overallPct + "%";
    barLabelElem.textContent = overallPct + "% Complete (" + completedTopics + "/" + totalTopics + " topics)";
    progressBarElem.style.width = overallPct + "%";

    // 2. Subject-wise Performance
    subjectListElem.innerHTML = "";

    // Build unique subjects map from both subjects list and topics
    const subjectMap = {};

    subs.forEach(function (s) {
        const trimmed = String(s).trim();
        if (trimmed && !subjectMap[trimmed]) {
            subjectMap[trimmed] = { total: 0, completed: 0, pending: 0 };
        }
    });

    topics.forEach(function (t) {
        const s = String(t.subject || "General").trim();
        if (!subjectMap[s]) {
            subjectMap[s] = { total: 0, completed: 0, pending: 0 };
        }
        subjectMap[s].total++;
        if (t.completed) {
            subjectMap[s].completed++;
        } else {
            subjectMap[s].pending++;
        }
    });

    const subjectKeys = Object.keys(subjectMap);

    if (subjectKeys.length === 0) {
        const emptyMsg = document.createElement("p");
        emptyMsg.style.color = "#64748b";
        emptyMsg.style.fontSize = "14px";
        emptyMsg.textContent = "No subjects added yet. Add subjects in Study Preferences to see subject performance.";
        subjectListElem.appendChild(emptyMsg);
    } else {
        subjectKeys.forEach(function (subjName) {
            const data = subjectMap[subjName];
            const pct = data.total === 0 ? 0 : Math.round((data.completed / data.total) * 100);

            const item = document.createElement("div");
            item.className = "subject-perf-item";

            const header = document.createElement("div");
            header.className = "subject-perf-header";

            const nameSpan = document.createElement("span");
            nameSpan.className = "subject-perf-name";
            nameSpan.textContent = "📚 " + subjName;
            header.appendChild(nameSpan);

            const pctSpan = document.createElement("span");
            pctSpan.className = "subject-perf-pct";
            pctSpan.textContent = pct + "%";
            pctSpan.style.color = pct >= 75 ? "#16a34a" : (pct >= 40 ? "#2563eb" : "#d97706");
            header.appendChild(pctSpan);

            item.appendChild(header);

            const sub = document.createElement("div");
            sub.className = "subject-perf-sub";
            if (data.total === 0) {
                sub.textContent = "0 topics added yet for this subject";
            } else {
                sub.textContent = data.completed + " of " + data.total + " completed (" + data.pending + " pending)";
            }
            item.appendChild(sub);

            const barContainer = document.createElement("div");
            barContainer.style.width = "100%";
            barContainer.style.height = "8px";
            barContainer.style.background = "#e2e8f0";
            barContainer.style.borderRadius = "6px";
            barContainer.style.overflow = "hidden";

            const barFill = document.createElement("div");
            barFill.style.height = "100%";
            barFill.style.width = pct + "%";
            barFill.style.background = pct >= 75 ? "#16a34a" : (pct >= 40 ? "#2563eb" : "#d97706");
            barFill.style.borderRadius = "6px";
            barFill.style.transition = "width 0.3s ease";
            barContainer.appendChild(barFill);

            item.appendChild(barContainer);

            subjectListElem.appendChild(item);
        });
    }

    // 3. Learning Insights & Personalized Recommendations
    insightsContainerElem.innerHTML = "";

    const activeSubjects = subjectKeys.filter(function (s) {
        return subjectMap[s].total > 0;
    });

    if (totalTopics === 0) {
        const noDataPill = document.createElement("div");
        noDataPill.className = "insight-pill insight-recommendation";
        noDataPill.textContent = "💡 Tip: Add your study topics in the Study Progress Tracker above to unlock real-time mastery analytics and learning recommendations.";
        insightsContainerElem.appendChild(noDataPill);
        return;
    }

    // A. Identify subject with highest completion percentage
    let bestSubject = null;
    let highestPct = -1;

    activeSubjects.forEach(function (s) {
        const data = subjectMap[s];
        const pct = Math.round((data.completed / data.total) * 100);
        if (pct > highestPct) {
            highestPct = pct;
            bestSubject = s;
        }
    });

    if (bestSubject && highestPct > 0) {
        const bestPill = document.createElement("div");
        bestPill.className = "insight-pill insight-best";
        const bData = subjectMap[bestSubject];
        bestPill.textContent = "🏆 Highest Completion: " + bestSubject + " (" + highestPct + "% complete — " + bData.completed + " of " + bData.total + " topics mastered).";
        insightsContainerElem.appendChild(bestPill);
    }

    // B. Identify subject needing the most attention
    let attentionSubject = null;
    let lowestPct = 101;
    let maxPending = -1;

    activeSubjects.forEach(function (s) {
        const data = subjectMap[s];
        if (data.pending > 0) {
            const pct = Math.round((data.completed / data.total) * 100);
            if (pct < lowestPct || (pct === lowestPct && data.pending > maxPending)) {
                lowestPct = pct;
                maxPending = data.pending;
                attentionSubject = s;
            }
        }
    });

    if (attentionSubject) {
        const attentionPill = document.createElement("div");
        attentionPill.className = "insight-pill insight-attention";
        const aData = subjectMap[attentionSubject];
        attentionPill.textContent = "⚠️ Needs Attention: " + attentionSubject + " has " + aData.pending + " pending topic" + (aData.pending === 1 ? "" : "s") + " (" + lowestPct + "% complete). Prioritize this subject in your next study blocks.";
        insightsContainerElem.appendChild(attentionPill);
    } else if (completedTopics === totalTopics && totalTopics > 0) {
        const allDonePill = document.createElement("div");
        allDonePill.className = "insight-pill insight-best";
        allDonePill.textContent = "🎉 Outstanding! All " + totalTopics + " tracked topics are completed. Focus your upcoming study sessions on full-length practice tests and revision.";
        insightsContainerElem.appendChild(allDonePill);
    }

    // C. Personalized recommendations based on actual pending topics
    const uncompletedTopics = topics.filter(function (t) { return !t.completed; });
    const recPill = document.createElement("div");
    recPill.className = "insight-pill insight-recommendation";

    if (uncompletedTopics.length > 0) {
        let targetTopic = null;
        if (attentionSubject) {
            targetTopic = uncompletedTopics.find(function (t) { return t.subject === attentionSubject; });
        }
        if (!targetTopic) {
            targetTopic = uncompletedTopics[0];
        }

        let recText = "📌 Immediate Next Goal: Study \"" + targetTopic.topic + "\" in " + targetTopic.subject + ".";

        const examDateInput = document.getElementById("examDate");
        if (examDateInput && examDateInput.value) {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const exam = new Date(examDateInput.value + "T00:00:00");
            if (!isNaN(exam.getTime())) {
                const daysLeft = Math.ceil((exam - today) / (1000 * 60 * 60 * 24));
                if (daysLeft > 0) {
                    recText += " With " + daysLeft + " day" + (daysLeft === 1 ? "" : "s") + " until your exam, completing this pending topic will quickly improve your readiness.";
                }
            }
        }

        recPill.textContent = recText;
    } else {
        recPill.textContent = "💡 Recommendation: Ask the Gemini AI Study Assistant to quiz you on key concepts to maintain long-term memory retention.";
    }

    insightsContainerElem.appendChild(recPill);
}

updateProgressSubjects();
displayProgressTopics();
updatePerformanceAnalytics();
saveStatus.textContent = "✅ Your saved data loaded successfully!";

const examDateInput = document.getElementById("examDate");
if (examDateInput) {
    examDateInput.addEventListener("change", function () {
        updatePerformanceAnalytics();
    });
}


// Save Student Data to Flask Backend

document.getElementById("saveStudentDataButton")
.addEventListener("click", async function () {

    const studentData = {
        studentName: document.getElementById("studentName").value.trim(),
        branch: document.getElementById("studentBranch").value,
        semester: document.getElementById("studentSemester").value,
        studyHours: document.getElementById("studyHours").value,
        examDate: document.getElementById("examDate").value,
        subjects: subjects,
        studyTopics: studyTopics
    };

    if (!studentData.studentName ||
        !studentData.branch ||
        !studentData.semester) {

        notifyStudent("Please fill your student details first!");
        return;
    }

    const saveStatus = document.getElementById("saveStatus");

    saveStatus.textContent = "Saving your data...";

    try {
        const response = await fetch("/api/save-student-data", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Profile-Token": localStorage.getItem("timewise-profile:" + studentData.studentName.toLowerCase()) || ""
            },
            body: JSON.stringify(studentData)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || "Unable to save data");
        }

        if (result.profileToken) {
            localStorage.setItem("timewise-profile:" + studentData.studentName.toLowerCase(), result.profileToken);
        }
        saveStatus.textContent = "✅ " + result.message;
        saveStatus.style.color = "green";

    } catch (error) {
        saveStatus.textContent = "❌ " + error.message;
        saveStatus.style.color = "red";
    }
});

// Load Student Data from Flask Backend

document.getElementById("loadStudentDataButton")
.addEventListener("click", async function () {

    const studentName =
        document.getElementById("studentName").value.trim();

    if (!studentName) {
        notifyStudent("Please enter your student name first!");
        return;
    }

    const saveStatus = document.getElementById("saveStatus");
    saveStatus.textContent = "Loading your data...";

    try {
        const profileToken = localStorage.getItem("timewise-profile:" + studentName.toLowerCase());
        if (!profileToken) throw new Error("Profile access key not found in this browser. Use the browser where you created your profile.");
        const response = await fetch("/api/get-student-data", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Profile-Token": profileToken },
            body: JSON.stringify({ studentName })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.message || "Unable to load data");
        }

        const data = result.data;

        document.getElementById("studentName").value = data.studentName || "";
        document.getElementById("studentBranch").value = data.branch || "";
        document.getElementById("studentSemester").value = data.semester || "";
        document.getElementById("studyHours").value = data.studyHours || "2";
        document.getElementById("examDate").value = data.examDate || "";

        subjects = Array.isArray(data.subjects) ? data.subjects : [];
        displaySubjects();

        studyTopics = Array.isArray(data.studyTopics) ? data.studyTopics : [];

        updateProgressSubjects();
        displayProgressTopics();

        saveStatus.textContent = "✅ Your saved data loaded successfully!";
        saveStatus.style.color = "green";

    } catch (error) {
        saveStatus.textContent = "❌ " + error.message;
        saveStatus.style.color = "red";
    }
});

// ==========================================
// Gemini AI Study Assistant Chat Widget
// ==========================================

const aiChatToggleBtn = document.getElementById("aiChatToggleBtn");
const aiChatPanel = document.getElementById("aiChatPanel");
const aiChatCloseBtn = document.getElementById("aiChatCloseBtn");
const aiChatMessages = document.getElementById("aiChatMessages");
const aiTypingIndicator = document.getElementById("aiTypingIndicator");
const aiChatInput = document.getElementById("aiChatInput");
const aiChatSendBtn = document.getElementById("aiChatSendBtn");
const aiPromptChips = document.querySelectorAll(".ai-prompt-chip");

let isAILoading = false;

// Toggle Chat Panel visibility
function setChatOpen(open) {
    aiChatPanel.classList.toggle("active", open);
    aiChatPanel.setAttribute("aria-hidden", String(!open));
    aiChatToggleBtn.setAttribute("aria-expanded", String(open));
    aiChatToggleBtn.setAttribute("aria-label", open ? "Close AI Study Assistant" : "Open AI Study Assistant");
    if (open) {
        aiChatInput.focus();
        aiChatMessages.scrollTop = aiChatMessages.scrollHeight;
    } else {
        aiChatToggleBtn.focus();
    }
}

aiChatPanel.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
        event.preventDefault();
        setChatOpen(false);
    }
});

aiChatToggleBtn.addEventListener("click", function () {
    setChatOpen(!aiChatPanel.classList.contains("active"));
});

aiChatCloseBtn.addEventListener("click", function () {
    setChatOpen(false);
});

// Auto-expand input textarea
aiChatInput.addEventListener("input", function () {
    this.style.height = "42px";
    this.style.height = Math.min(this.scrollHeight, 100) + "px";
});

// Enter key sends message, Shift+Enter for new line
aiChatInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendAIMessage();
    }
});

aiChatSendBtn.addEventListener("click", function () {
    sendAIMessage();
});

// Gather actual student academic profile from the dashboard
function getStudentAcademicContext() {
    const branchElem = document.getElementById("studentBranch");
    const semesterElem = document.getElementById("studentSemester");
    const examDateElem = document.getElementById("examDate");
    const studyHoursElem = document.getElementById("studyHours");

    const branch = branchElem ? branchElem.value : "";
    const semester = semesterElem ? semesterElem.value : "";
    const examDate = examDateElem ? examDateElem.value : "";
    const availableHours = studyHoursElem ? studyHoursElem.value : "";

    // Use actual existing studyTopics array: filter only incomplete topics
    const pending = (typeof studyTopics !== "undefined" && Array.isArray(studyTopics))
        ? studyTopics.filter(function (item) { return !item.completed; })
        : [];

    // Use actual existing subjects array
    const currentSubjects = (typeof subjects !== "undefined" && Array.isArray(subjects))
        ? subjects
        : [];

    return {
        branch: branch,
        semester: semester,
        subjects: currentSubjects,
        pendingTopics: pending,
        examDate: examDate,
        availableHours: availableHours
    };
}

// Safely append a message to chat using textContent (NEVER innerHTML)
function appendAIMessage(text, sender, isError) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "ai-msg";

    if (sender === "user") {
        msgDiv.classList.add("ai-msg-user");
    } else if (isError) {
        msgDiv.classList.add("ai-msg-error");
    } else {
        msgDiv.classList.add("ai-msg-assistant");
    }

    msgDiv.textContent = text;
    aiChatMessages.appendChild(msgDiv);
    aiChatMessages.scrollTop = aiChatMessages.scrollHeight;
}

// Set loading UI state
function setAILoading(loading) {
    isAILoading = loading;
    aiChatSendBtn.disabled = loading;
    aiChatInput.disabled = loading;
    aiTypingIndicator.style.display = loading ? "inline-flex" : "none";
    if (loading) {
        aiChatMessages.scrollTop = aiChatMessages.scrollHeight;
    }
}

// Send user message to Gemini backend
async function sendAIMessage(presetMessage) {
    const message = (presetMessage || aiChatInput.value).trim();

    if (!message) {
        return;
    }

    if (isAILoading) {
        return;
    }

    // Ensure chat panel is open
    if (!aiChatPanel.classList.contains("active")) {
        setChatOpen(true);
    }

    // Display user message in chat
    appendAIMessage(message, "user", false);
    aiChatInput.value = "";
    aiChatInput.style.height = "42px";

    setAILoading(true);

    const context = getStudentAcademicContext();
    const payload = {
        message: message,
        branch: context.branch,
        semester: context.semester,
        subjects: context.subjects,
        pendingTopics: context.pendingTopics,
        examDate: context.examDate,
        availableHours: context.availableHours
    };

    try {
        const response = await fetch("/api/ai/study-assistant", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json().catch(function () { return {}; });

        if (!response.ok) {
            const errorMsg = data.error || ("Server error (" + response.status + "): Unable to get response.");
            appendAIMessage("⚠️ " + errorMsg, "assistant", true);
        } else if (data.reply) {
            appendAIMessage(data.reply, "assistant", false);
        } else {
            appendAIMessage("⚠️ The AI service returned an empty response. Please try rephrasing your question.", "assistant", true);
        }
    } catch (networkError) {
        appendAIMessage("⚠️ Network connection error. Please ensure your internet connection and Flask server are active.", "assistant", true);
    } finally {
        setAILoading(false);
        aiChatInput.focus();
    }
}

// Quick prompt suggestions tailored to actual student state
aiPromptChips.forEach(function (chip) {
    chip.addEventListener("click", function () {
        const promptType = this.getAttribute("data-prompt");
        const context = getStudentAcademicContext();
        let promptText = "";

        if (promptType === "explain") {
            if (context.pendingTopics.length > 0) {
                const topicItem = context.pendingTopics[0];
                promptText = "Can you explain the topic \"" + topicItem.topic + "\" in " + topicItem.subject + " step-by-step with an engineering example?";
            } else if (context.subjects.length > 0) {
                promptText = "Can you explain a key fundamental concept in " + context.subjects[0] + " with an intuitive example?";
            } else {
                promptText = "Can you explain a difficult engineering concept step-by-step with an example?";
            }
        } else if (promptType === "strategy") {
            if (context.examDate) {
                promptText = "Given my upcoming exam on " + context.examDate + " and " + (context.availableHours || "4") + " hours/day of study, what is the best revision strategy for my subjects?";
            } else {
                promptText = "Can you recommend an effective daily revision strategy and schedule for my engineering subjects?";
            }
        } else if (promptType === "quiz") {
            if (context.pendingTopics.length > 0) {
                const topicNames = context.pendingTopics.slice(0, 3).map(function (t) {
                    return t.subject + " - " + t.topic;
                }).join(", ");
                promptText = "Can you test my knowledge with a 3-question conceptual quiz on my pending topics: " + topicNames + "?";
            } else if (context.subjects.length > 0) {
                promptText = "Can you quiz me with 3 conceptual questions on " + context.subjects.join(", ") + " to test my fundamentals?";
            } else {
                promptText = "Can you quiz me with 3 conceptual questions on engineering fundamentals?";
            }
        } else if (promptType === "prepare") {
            if (context.subjects.length > 0) {
                promptText = "What are the most effective high-yield exam preparation and active recall techniques for " + context.subjects.join(", ") + "?";
            } else {
                promptText = "What are the most effective high-yield exam preparation techniques for engineering semester exams?";
            }
        }

        if (promptText) {
            sendAIMessage(promptText);
        }
    });
});
