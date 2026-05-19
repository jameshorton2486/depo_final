        function validateUFMField(inputEl, label) {
            const val = inputEl.value.trim();
            const badge = inputEl.parentElement.querySelector('.ufm-val-badge');

            // Map inputs to state case schema
            const idMap = {
                'ufmCause': 'cause',
                'ufmStyle': 'caption',
                'ufmCourt': 'court',
                'ufmCounty': 'county',
                'ufmState': 'state',
                'ufmWitness': 'deponent',
                'ufmDate': 'date',
                'ufmStartTime': 'startTime',
                'ufmEndTime': 'endTime',
                'ufmAddress': 'address',
                'ufmCSRName': 'csrName',
                'ufmCSRLicense': 'csrLicense',
                'ufmFirmReg': 'firmReg',
                'ufmCSRCertExp': 'csrCertExp',
                'ufmCustodialName': 'custodialName',
                'ufmRequestingParty': 'requestingParty'
            };

            const stateField = idMap[inputEl.id];
            if (stateField) {
                state.caseInfo[stateField] = val;
            }

            if (val === "") {
                inputEl.className = "w-full bg-slate-900 border border-red-500/30 text-xs px-2.5 py-1 rounded-lg text-white focus:outline-none";
                if (badge) {
                    badge.innerText = "MISSING";
                    badge.className = "ufm-val-badge absolute right-2 top-6 text-[8px] px-1 py-0.2 rounded bg-red-500/10 text-red-400";
                }
            } else {
                inputEl.className = "w-full bg-slate-900 border border-emerald-500/30 text-xs px-2.5 py-1 rounded-lg text-white focus:outline-none";
                if (badge) {
                    badge.innerText = "✓ VERIFIED";
                    badge.className = "ufm-val-badge absolute right-2 top-6 text-[8px] px-1 py-0.2 rounded bg-emerald-500/10 text-emerald-400";
                }
            }

            // Sync legacy global mirrors if present (no-op when those nodes don't exist in current shell)
            if (stateField === 'caption') {
                const mirror = document.getElementById('caseCaption');
                if (mirror) mirror.value = val;
            }
            if (stateField === 'deponent') {
                const mirror = document.getElementById('caseDeponent');
                if (mirror) mirror.value = val;
            }

            checkSchemaValidationStatus();
        }

        // Run validation calculations over all fields
        function checkSchemaValidationStatus() {
            const summaryBadge = document.getElementById('validationSummaryBadge');
            if (!summaryBadge) return;

            const fields = [
                'ufmCause', 'ufmStyle', 'ufmCourt', 'ufmCounty', 'ufmState',
                'ufmWitness', 'ufmDate', 'ufmStartTime', 'ufmEndTime', 'ufmAddress',
                'ufmCSRName', 'ufmCSRLicense', 'ufmFirmReg', 'ufmCSRCertExp',
                'ufmCustodialName', 'ufmRequestingParty'
            ];

            let incomplete = false;
            fields.forEach(id => {
                const el = document.getElementById(id);
                if (el && el.value.trim() === "") {
                    incomplete = true;
                }
            });

            if (incomplete) {
                summaryBadge.innerText = "⚠️ SCHEMA INCOMPLETE";
                summaryBadge.className = "text-[10px] px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 font-bold";
            } else {
                summaryBadge.innerText = "✓ ALL FIELDS VERIFIED";
                summaryBadge.className = "text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold";
            }
        }

        // Simulated AI Legal notes parser engine
        function runAILegalParser() {
            const rawNotes = document.getElementById('rawIntakeNotes').value;
            if (!rawNotes.trim()) {
                showToast("Intake notes workspace is empty. Please enter text.", "red");
                return;
            }

            showToast("Parsing notice text utilizing UFM extraction matrices...", "cyan");
            addProvenanceRecord("Notice Parser Sandbox", "Initiated natural language regex parser.", "system");

            // Simple mock extraction logic scanning common structures
            setTimeout(() => {
                const docFields = {
                    'ufmCause': '2024-CI-28593',
                    'ufmStyle': 'SARAH JENKINS vs. NEXUS PHARMA INC.',
                    'ufmCourt': '101st Judicial District',
                    'ufmCounty': 'Dallas County',
                    'ufmState': 'Texas',
                    'ufmWitness': 'Dr. Donald Leifer',
                    'ufmDate': '2026-05-19',
                    'ufmStartTime': '10:00 AM',
                    'ufmEndTime': '12:30 PM',
                    'ufmAddress': '201 Main Street, Suite 600, Fort Worth, Texas 76102',
                    'ufmCSRName': 'Richard Vance, CSR',
                    'ufmCSRLicense': '3465',
                    'ufmFirmReg': '10698',
                    'ufmCSRCertExp': '2027-12-31',
                    'ufmCustodialName': 'Ms. Elizabeth R. Flora, Esq.',
                    'ufmRequestingParty': 'Vance & Partners LLP'
                };

                for (const [id, value] of Object.entries(docFields)) {
                    const input = document.getElementById(id);
                    if (input) {
                        input.value = value;
                        validateUFMField(input, id);
                        input.classList.add('animate-flash');
                        setTimeout(() => input.classList.remove('animate-flash'), 1500);
                    }
                }

                // Add extraction dictionary items
                state.correctionsMemory.push({ original: "doc leifer", replacement: "Dr. Donald Leifer", scope: "case" });
                state.correctionsMemory.push({ original: "neuroma", replacement: "Acoustic Neuroma", scope: "case" });

                renderAllStateComponents();
                renderUFMTermsTable();
                showToast("Acoustic entities parsed. UFM Verification Board complete!", "emerald");
                addProvenanceRecord("Notice Parser Sandbox", "Extracted 16/16 legal fields successfully.", "ai");
            }, 1200);
        }

        // Repopulate UFM form inputs from state.caseInfo (e.g. when revisiting Stage 1)
        function hydrateUFMFormFromState() {
            const reverseMap = {
                'ufmCause': 'cause',
                'ufmStyle': 'caption',
                'ufmCourt': 'court',
                'ufmCounty': 'county',
                'ufmState': 'state',
                'ufmWitness': 'deponent',
                'ufmDate': 'date',
                'ufmStartTime': 'startTime',
                'ufmEndTime': 'endTime',
                'ufmAddress': 'address',
                'ufmCSRName': 'csrName',
                'ufmCSRLicense': 'csrLicense',
                'ufmFirmReg': 'firmReg',
                'ufmCSRCertExp': 'csrCertExp',
                'ufmCustodialName': 'custodialName',
                'ufmRequestingParty': 'requestingParty'
            };
            for (const [id, stateField] of Object.entries(reverseMap)) {
                const el = document.getElementById(id);
                if (!el) continue;
                const val = state.caseInfo[stateField];
                if (val) {
                    el.value = val;
                    validateUFMField(el, id);
                }
            }
        }

        function renderUFMTermsTable() {
            const tbody = document.getElementById('ufmTermsTableBody');
            const countEl = document.getElementById('ufmTermsCount');
            if (!tbody) return;

            const rows = [];
            if (state.caseInfo.deponent) {
                rows.push({ term: state.caseInfo.deponent, category: 'Deponent', source: 'Notice parser', boost: 1.5 });
            }
            if (state.caseInfo.csrName) {
                rows.push({ term: state.caseInfo.csrName, category: 'Reporter', source: 'Notice parser', boost: 1.0 });
            }
            if (state.caseInfo.custodialName) {
                rows.push({ term: state.caseInfo.custodialName, category: 'Attorney', source: 'Notice parser', boost: 1.2 });
            }
            if (state.caseInfo.requestingParty) {
                rows.push({ term: state.caseInfo.requestingParty, category: 'Firm', source: 'Notice parser', boost: 1.0 });
            }
            (state.correctionsMemory || []).forEach(corr => {
                rows.push({
                    term: corr.replacement,
                    category: 'Medical',
                    source: corr.scope === 'global' ? 'Learned' : 'Notice parser',
                    boost: 1.5
                });
            });

            tbody.innerHTML = "";
            if (rows.length === 0) {
                tbody.innerHTML = `<tr><td colspan="4" class="py-3 px-3 text-center text-slate-600 italic">No terms parsed yet. Run AI Notes Parser to populate.</td></tr>`;
            } else {
                rows.forEach(r => {
                    const tr = document.createElement('tr');
                    tr.className = "border-t border-slate-900 hover:bg-slate-900/40 transition-all";
                    tr.innerHTML = `
                        <td class="py-1.5 px-3 text-white">${r.term}</td>
                        <td class="py-1.5 px-3"><span class="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">${r.category}</span></td>
                        <td class="py-1.5 px-3 text-slate-400">${r.source}</td>
                        <td class="py-1.5 px-3 text-right text-emerald-400">${r.boost.toFixed(1)}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
            if (countEl) countEl.innerText = `${rows.length} term${rows.length === 1 ? '' : 's'}`;
        }

        // Proceed confirmation check
        function confirmProceedWithSchemaCheck() {
            const summaryBadge = document.getElementById('validationSummaryBadge');
            if (summaryBadge.innerText.includes("INCOMPLETE")) {
                showToast("Warning: Some mandatory UFM variables are blank. UFM generation may fail.", "amber");
            }
            goToStage(2);
        }

        // goToStage / getStageName / triggerFileInput live in app.js and ui.js (Phase A.2 extraction)

        function handleAudioSelect(input) {
            if (input.files && input.files[0]) {
                document.getElementById('audioLabel').innerText = `File ready: ${input.files[0].name}`;
                document.getElementById('topCaseLabel').innerText = input.files[0].name;

                // Also load this into Section B queue as a primary element automatically
                addSingleFileToQueue(input.files[0]);
            }
        }

        // Notice of Deposition Parser simulation
        function simulateNODParsing(input) {
            if (input.files && input.files[0]) {
                document.getElementById('nodLabel').innerText = `Notice parsed: ${input.files[0].name}`;
                showToast("Parsing uploaded notice...", "cyan");
                runAILegalParser();
            }
        }

        function handleDepoNotesSelect(input) {
            if (input.files && input.files[0]) {
                const file = input.files[0];
                document.getElementById('depoNotesLabel').innerText = `Notes attached: ${file.name}`;
                addProvenanceRecord && addProvenanceRecord(
                    "Deposition Notes Attached",
                    `Court reporter notes file linked: ${file.name}`,
                    "user"
                );
                showToast && showToast(`Deposition notes attached: ${file.name}`, "emerald");
            }
        }

        function openKeyTermsJsonModal() {
            const payload = buildKeytermsPayload();
            const pre = document.getElementById('keytermsJsonContent');
            if (pre) pre.textContent = JSON.stringify(payload, null, 2);
            const modal = document.getElementById('keytermsJsonModal');
            if (modal) modal.classList.remove('hidden');
        }

        function closeKeyTermsJsonModal() {
            const modal = document.getElementById('keytermsJsonModal');
            if (modal) modal.classList.add('hidden');
        }

        function copyKeyTermsJson() {
            const pre = document.getElementById('keytermsJsonContent');
            if (pre && navigator.clipboard) {
                navigator.clipboard.writeText(pre.textContent).then(() => {
                    showToast && showToast("Keyterms JSON copied to clipboard.", "emerald");
                });
            }
        }

        function buildKeytermsPayload() {
            const terms = [];
            if (state.caseInfo.deponent) terms.push({ term: state.caseInfo.deponent, boost: 1.5, source: 'notice_parser' });
            if (state.caseInfo.csrName) terms.push({ term: state.caseInfo.csrName, boost: 1.0, source: 'notice_parser' });
            if (state.caseInfo.custodialName) terms.push({ term: state.caseInfo.custodialName, boost: 1.2, source: 'notice_parser' });
            if (state.caseInfo.requestingParty) terms.push({ term: state.caseInfo.requestingParty, boost: 1.0, source: 'notice_parser' });
            (state.correctionsMemory || []).forEach(c => terms.push({ term: c.replacement, boost: 1.5, source: c.scope === 'global' ? 'learned' : 'notice_parser' }));
            return {
                case_id: 'pending_phase_b',
                case_caption: state.caseInfo.caption || null,
                cause_number: state.caseInfo.cause || null,
                generated_at: new Date().toISOString(),
                keyterms: terms
            };
        }


window.validateUFMField = validateUFMField;
window.checkSchemaValidationStatus = checkSchemaValidationStatus;
window.runAILegalParser = runAILegalParser;
window.hydrateUFMFormFromState = hydrateUFMFormFromState;
window.renderUFMTermsTable = renderUFMTermsTable;
window.confirmProceedWithSchemaCheck = confirmProceedWithSchemaCheck;
window.handleAudioSelect = handleAudioSelect;
window.simulateNODParsing = simulateNODParsing;
window.handleDepoNotesSelect = handleDepoNotesSelect;
window.openKeyTermsJsonModal = openKeyTermsJsonModal;
window.closeKeyTermsJsonModal = closeKeyTermsJsonModal;
window.copyKeyTermsJson = copyKeyTermsJson;
window.buildKeytermsPayload = buildKeytermsPayload;
