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

            // Sync global layouts
            if (stateField === 'caption') {
                document.getElementById('caseCaption').value = val;
            }
            if (stateField === 'deponent') {
                document.getElementById('caseDeponent').value = val;
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

        // Stage Management
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

        function getStageName(num) {
            const names = ["Case Intake", "Transcripts Engine", "Living Transcript Workspace", "Citation Insertion Pages", "Case Certification", "Format Export"];
            return names[num - 1];
        }

        // Trigger hidden inputs
        function triggerFileInput(id) {
            document.getElementById(id).click();
        }

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
window.renderSpellingDictionarySeeds = renderSpellingDictionarySeeds;
window.confirmProceedWithSchemaCheck = confirmProceedWithSchemaCheck;
window.handleAudioSelect = handleAudioSelect;
window.simulateNODParsing = simulateNODParsing;
