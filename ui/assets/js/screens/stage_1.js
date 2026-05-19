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
                inputEl.className = "w-full bg-slate-900 border border-red-500/30 text-xs px-2.5 py-1.5 rounded-lg text-white focus:outline-none";
                if (badge) {
                    badge.innerText = "MISSING";
                    badge.className = "ufm-val-badge absolute right-2 top-6 text-[8px] px-1 py-0.2 rounded bg-red-500/10 text-red-400";
                }
            } else {
                inputEl.className = "w-full bg-slate-900 border border-emerald-500/30 text-xs px-2.5 py-1.5 rounded-lg text-white focus:outline-none";
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

        // Render intake seeds
        function renderSpellingDictionarySeeds() {
            const list = document.getElementById('intakeEntitiesList');
            if (!list) return;
            list.innerHTML = "";

            const seeds = [
                { type: 'Deponent', val: state.caseInfo.deponent || "Dr. Donald Leifer", desc: "Expert Neurosurgeon Witness" },
                { type: 'Attorneys', val: state.caseInfo.custodialName || "Richard Vance, Esq.", desc: "Host Counsel / PLAINTIFF REPRESENTATIVE" },
                { type: 'Acoustic terminology', val: "Acoustic Neuroma", desc: "Surgical reference from para 4" }
            ];

            seeds.forEach(seed => {
                const card = document.createElement('div');
                card.className = "bg-slate-950/60 p-3 rounded-xl border border-slate-800/80";
                card.innerHTML = `
                    <span class="text-[9px] font-bold tracking-wider uppercase text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded">${seed.type}</span>
                    <p class="text-xs font-semibold text-white mt-1 font-mono">${seed.val}</p>
                    <p class="text-[10px] text-slate-500 mt-0.5">${seed.desc}</p>
                `;
                list.appendChild(card);
            });
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


window.validateUFMField = validateUFMField;
window.checkSchemaValidationStatus = checkSchemaValidationStatus;
window.runAILegalParser = runAILegalParser;
window.hydrateUFMFormFromState = hydrateUFMFormFromState;
window.renderSpellingDictionarySeeds = renderSpellingDictionarySeeds;
window.confirmProceedWithSchemaCheck = confirmProceedWithSchemaCheck;
window.handleAudioSelect = handleAudioSelect;
window.simulateNODParsing = simulateNODParsing;
