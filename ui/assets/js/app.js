        const initialRawNotesSeed = `REPORTER SCHEDULING NOTE:
Deposition of Dr. Donald Leifer held on May 19, 2026.
Case Caption: SARAH JENKINS vs. NEXUS PHARMA INC.
Cause No. 2024-CI-28593
Court: 101st Judicial District of Dallas County, Texas
Start at 10:00 AM, finished at 12:30 PM.
Deposition location: Lexitas Fort Worth, 201 Main Street, Suite 600, Fort Worth, Texas 76102.
Court Reporter: Richard Vance, CSR License 3465, expiration 2027-12-31, Firm Registration 10698.
Custodial Attorney: Ms. Elizabeth R. Flora, Esq. representing Plaintiff sarah jenkins.
Acoustic spellings to sync: Acoustic Neuroma, cranial, Leifer.`;

        function seedRawIntakeNotes() {
            const rawNotesField = document.getElementById('rawIntakeNotes');
            if (rawNotesField && !rawNotesField.value.trim()) {
                rawNotesField.value = initialRawNotesSeed;
            }
        }

        // Window Initializer
        window.onload = function() {
            seedRawIntakeNotes();
            renderAllStateComponents();
            if (document.getElementById('validationSummaryBadge')) {
                checkSchemaValidationStatus();
            }
            showToast("Workspace initialized. Texas UFM layout active.");
        };

        // Complete state rendering dispatch
        function renderAllStateComponents() {
            if (document.getElementById('speakersList')) renderSpeakersList();
            if (document.getElementById('correctionsMemoryContainer')) renderCorrectionMemory();
            if (document.getElementById('provenanceLogContainer')) renderProvenanceTimeline();
            if (document.getElementById('transcriptLinesContainer')) compileAndRenderTranscript();
            if (document.getElementById('exhibitsIndexList')) renderExhibitsIndex();
            if (document.getElementById('flagCount')) updateStatsBar();
            if (document.getElementById('sequentialQueueList')) renderFileQueue();
            if (document.getElementById('intakeEntitiesList')) renderSpellingDictionarySeeds();
        }


        function goToStage(stageNum) {
            if (state.caseInfo.certified && stageNum < 5) {
                showToast("This transcript is CERTIFIED and LOCKED. Request unlock to edit.", "red");
                return;
            }

            // Update tab highlights
            for (let i = 1; i <= 6; i++) {
                const tab = document.getElementById(`stageTab${i}`);
                if (!tab) continue;
                if (i === stageNum) {
                    tab.className = "px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 shadow-sm";
                } else {
                    tab.className = "px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all text-slate-400 hover:text-slate-200 hover:bg-slate-800";
                }
            }
            state.currentStage = stageNum;
            loadScreen(stageNum);
            showToast(`Stage loaded: ${getStageName(stageNum)}`);
        }

        function updateStatsBar() {
            const suggestionsCount = state.transcriptLines.filter(l => l.hasSuggestion).length;
            const flagCount = document.getElementById('flagCount');
            if (!flagCount) return;
            flagCount.innerText = `${suggestionsCount} pending flags`;
        }


        function simulateSave() {
            showToast("Saving living transcript arrays to local IndexedDB...", "emerald");
        }

        window.addEventListener("screen:loaded", (e) => {
            const stageNum = e.detail.stageNum;
            // Re-bind handlers and re-render data into the freshly-mounted screen
            try {
                if (stageNum === 1) {
                    seedRawIntakeNotes();
                    hydrateUFMFormFromState && hydrateUFMFormFromState();
                    renderSpellingDictionarySeeds && renderSpellingDictionarySeeds();
                    checkSchemaValidationStatus && checkSchemaValidationStatus();
                } else if (stageNum === 2) {
                    renderFileQueue && renderFileQueue();
                } else if (stageNum === 3) {
                    compileAndRenderTranscript && compileAndRenderTranscript();
                    renderSpeakersList && renderSpeakersList();
                    renderCorrectionMemory && renderCorrectionMemory();
                    renderProvenanceTimeline && renderProvenanceTimeline();
                    updateStatsBar && updateStatsBar();
                } else if (stageNum === 4) {
                    renderExhibitsIndex && renderExhibitsIndex();
                } else if (stageNum === 5) {
                    // If already certified, show the sealed card instead of the sign form
                    if (state.caseInfo.certified) {
                        const pre = document.getElementById('certPreLock');
                        const post = document.getElementById('certPostLock');
                        const sigOut = document.getElementById('renderedSignatory');
                        if (pre) pre.classList.add('hidden');
                        if (post) post.classList.remove('hidden');
                        if (sigOut && state.caseInfo.signature) sigOut.innerText = state.caseInfo.signature;
                    }
                }
            } catch (err) {
                console.warn(`Render error for stage ${stageNum}:`, err);
            }
        });

window.seedRawIntakeNotes = seedRawIntakeNotes;
window.renderAllStateComponents = renderAllStateComponents;
window.goToStage = goToStage;
window.updateStatsBar = updateStatsBar;
window.simulateSave = simulateSave;
