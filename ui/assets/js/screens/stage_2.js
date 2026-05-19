        function addFilesToIngestionQueue(input) {
            if (input.files) {
                for (let i = 0; i < input.files.length; i++) {
                    addSingleFileToQueue(input.files[i]);
                }
                showToast(`Added ${input.files.length} file(s) to sequence queue.`, "indigo");
            }
        }

        function addSingleFileToQueue(file) {
            const fileId = `file-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
            state.fileQueue.push({
                id: fileId,
                name: file.name,
                size: (file.size / (1024 * 1024)).toFixed(1) + " MB",
                status: "Awaiting Ingestion",
                progress: 0
            });
            renderFileQueue();
        }

        // Reorganize files sequentially in the queue list
        function moveQueueItem(index, direction) {
            const targetIndex = index + direction;
            if (targetIndex < 0 || targetIndex >= state.fileQueue.length) return; // Out of bounds

            // Swap positions
            const temp = state.fileQueue[index];
            state.fileQueue[index] = state.fileQueue[targetIndex];
            state.fileQueue[targetIndex] = temp;

            renderFileQueue();
            showToast("Chronological sequence updated.");
        }

        function renderFileQueue() {
            const list = document.getElementById('sequentialQueueList');
            const submitBtn = document.getElementById('btnIngestQueue');
            if (!list || !submitBtn) return;
            list.innerHTML = "";

            if (state.fileQueue.length === 0) {
                list.innerHTML = `<p class="text-xs text-slate-600 italic text-center py-4 bg-slate-950/40 rounded-xl border border-slate-850 font-sans">In-order queue is empty. Drag or browse files above.</p>`;
                submitBtn.disabled = true;
                return;
            }

            submitBtn.disabled = false;

            state.fileQueue.forEach((file, index) => {
                const item = document.createElement('div');
                item.className = "flex flex-col bg-slate-950 p-3 rounded-xl border border-slate-850 hover:border-slate-800 transition-all text-xs gap-2";

                let statusBadgeColor = "text-slate-400 bg-slate-900";
                if (file.status === "Completed") statusBadgeColor = "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20";
                if (file.status === "Processing...") statusBadgeColor = "text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 animate-pulse";

                // Move button state
                const isFirst = index === 0;
                const isLast = index === state.fileQueue.length - 1;

                item.innerHTML = `
                    <div class="flex items-center justify-between gap-3">
                        <div class="flex items-center gap-3">
                            <div class="w-5 h-5 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-[10px] font-bold text-slate-400">
                                ${index + 1}
                            </div>
                            <div class="truncate">
                                <p class="font-mono text-white truncate max-w-xs md:max-w-md">${file.name}</p>
                                <p class="text-[10px] text-slate-500">${file.size}</p>
                            </div>
                        </div>
                        <div class="flex items-center gap-1.5">
                            <!-- Move Controls -->
                            <div class="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 mr-1">
                                <button onclick="moveQueueItem(${index}, -1)" ${isFirst ? 'disabled style="opacity:0.3"' : ''} class="p-1 hover:text-white text-slate-500 transition-all font-bold text-[10px]" title="Move Up">▲</button>
                                <div class="w-px h-3 bg-slate-800 mx-0.5"></div>
                                <button onclick="moveQueueItem(${index}, 1)" ${isLast ? 'disabled style="opacity:0.3"' : ''} class="p-1 hover:text-white text-slate-500 transition-all font-bold text-[10px]" title="Move Down">▼</button>
                            </div>

                            <span class="px-2 py-0.5 rounded text-[9px] font-semibold uppercase ${statusBadgeColor}">${file.status}</span>
                            <button onclick="removeFileFromQueue('${file.id}')" class="text-slate-500 hover:text-red-400 p-1 font-bold text-sm transition-all" title="Remove File">&times;</button>
                        </div>
                    </div>
                    <!-- Inline File Progress bar mapping live metrics -->
                    ${file.status === "Processing..." || file.status === "Completed" ? `
                    <div class="w-full bg-slate-900 h-1 rounded-full overflow-hidden mt-1">
                        <div class="bg-indigo-500 h-full transition-all duration-300" style="width: ${file.progress}%"></div>
                    </div>
                    ` : ''}
                `;
                list.appendChild(item);
            });
        }

        function removeFileFromQueue(id) {
            state.fileQueue = state.fileQueue.filter(f => f.id !== id);
            renderFileQueue();
            showToast("File removed from list.");
        }

        function clearAllQueues() {
            state.fileQueue = [];
            renderFileQueue();
            showToast("Ingestion sequence queue reset.");
        }

        // Interactive Mic Gain Testing simulation
        function testGainAndAudio() {
            const container = document.getElementById('liveGainContainer');
            container.classList.remove('hidden');
            showToast("Testing local sound card gain boundaries...", "indigo");

            let ticks = 0;
            const timer = setInterval(() => {
                const randomGain = -10 - Math.random() * 45; // Simulated DB levels
                const fillPercent = Math.max(10, 100 + (randomGain * 1.5)); // Map to percentage

                document.getElementById('gainLevelFill').style.width = `${fillPercent}%`;
                document.getElementById('dbValueLabel').innerText = `${randomGain.toFixed(1)} dBFS`;

                if (randomGain > -15) {
                    document.getElementById('micDiagnosticLevel').className = "w-1.5 h-1.5 rounded-full bg-red-500 animate-ping";
                } else if (randomGain > -35) {
                    document.getElementById('micDiagnosticLevel').className = "w-1.5 h-1.5 rounded-full bg-emerald-500";
                } else {
                    document.getElementById('micDiagnosticLevel').className = "w-1.5 h-1.5 rounded-full bg-amber-500";
                }

                ticks++;
                if (ticks > 40) {
                    clearInterval(timer);
                    container.classList.add('hidden');
                    showToast("Signal diagnostics completed successfully.", "emerald");
                }
            }, 100);
        }

        // Execute sequential queue processing loop with advanced ETA algorithms
        function startSequentialIngestion() {
            if (state.fileQueue.length === 0 || state.isQueueProcessing) return;

            state.isQueueProcessing = true;
            document.getElementById('btnIngestQueue').disabled = true;

            const logs = document.getElementById('sequentialLogs');
            const progressContainer = document.getElementById('sequentialProgressBar');
            const fill = document.getElementById('queueProgressFill');
            const percentLabel = document.getElementById('queueProgressPercent');
            const label = document.getElementById('queueProgressLabel');

            // Dynamic Metrics elements
            const statTimeElapsed = document.getElementById('statTimeElapsed');
            const statTimeRemaining = document.getElementById('statTimeRemaining');
            const statSpeedRatio = document.getElementById('statSpeedRatio');

            logs.classList.remove('hidden');
            progressContainer.classList.remove('hidden');
            logs.innerHTML = "<p class='text-indigo-400'>> Initializing chronological multi-file pipeline...</p>";

            let currentFileIdx = 0;
            state.elapsedProcessTime = 0;

            // Start master elapsed timer ticker
            state.elapsedTimerInterval = setInterval(() => {
                state.elapsedProcessTime += 0.1;
                statTimeElapsed.innerText = `${state.elapsedProcessTime.toFixed(1)}s`;
            }, 100);

            function processNextFile() {
                if (currentFileIdx >= state.fileQueue.length) {
                    // Entire queue finished
                    clearInterval(state.elapsedTimerInterval);
                    state.isQueueProcessing = false;
                    showToast("All media files in sequence processed and compiled!", "emerald");
                    addProvenanceRecord("Sequential File Compiler", `Successfully compiled ${state.fileQueue.length} files into living transcript layer.`, "system");

                    // Reset diagnostic stats
                    statTimeRemaining.innerText = "Completed";
                    statSpeedRatio.className = "text-emerald-400 font-bold";
                    statSpeedRatio.innerText = "All Transcripts Synced";

                    // Automatically add mock lines from batch sequence to display in Stage 3
                    appendChronologicalMockSegments();

                    setTimeout(() => {
                        goToStage(3);
                    }, 1500);
                    return;
                }

                const currentFile = state.fileQueue[currentFileIdx];
                currentFile.status = "Processing...";
                renderFileQueue();

                label.innerText = `Ingesting File ${currentFileIdx + 1} of ${state.fileQueue.length}: ${currentFile.name}`;

                const p = document.createElement('p');
                p.className = "text-slate-400";
                p.innerText = `> Connecting ${currentFile.name} to Deepgram Nova-3 engine...`;
                logs.appendChild(p);
                logs.scrollTop = logs.scrollHeight;

                let fileProgress = 0;
                const fileInterval = setInterval(() => {
                    fileProgress += 10;
                    currentFile.progress = fileProgress;

                    // Aggregate Progress calculation
                    const aggregateProgress = ((currentFileIdx * 100 + fileProgress) / (state.fileQueue.length * 100)) * 100;
                    fill.style.width = `${aggregateProgress}%`;
                    percentLabel.innerText = `${Math.round(aggregateProgress)}%`;

                    // Dynamic Speed and ETA predictions
                    const speedMultiplier = 8.0 + Math.random() * 2.5; // realistic fluctuating processor speed
                    statSpeedRatio.innerText = `${speedMultiplier.toFixed(1)}x Real-Time`;

                    // Calculate ETA in seconds remaining
                    const remainingPercent = 100 - aggregateProgress;
                    const etaEstimatedSeconds = Math.max(1, Math.round((state.elapsedProcessTime / aggregateProgress) * remainingPercent));
                    statTimeRemaining.innerText = `${etaEstimatedSeconds}s left`;

                    renderFileQueue();

                    if (fileProgress === 50) {
                        const logText = document.createElement('p');
                        logText.className = "text-slate-500";
                        logText.innerText = `> Diarizing speaker vocal tracks on [${currentFile.name}]...`;
                        logs.appendChild(logText);
                    }

                    if (fileProgress >= 100) {
                        clearInterval(fileInterval);
                        currentFile.status = "Completed";
                        currentFile.progress = 100;
                        renderFileQueue();

                        const completionLog = document.createElement('p');
                        completionLog.className = "text-emerald-400 font-semibold";
                        completionLog.innerText = `> Ingest complete for [${currentFile.name}]. Raw layer locked.`;
                        logs.appendChild(completionLog);

                        currentFileIdx++;
                        setTimeout(processNextFile, 400);
                    }
                }, 250);
            }

            processNextFile();
        }

        // Dynamically add processed file sequence segments into workspace
        function appendChronologicalMockSegments() {
            showToast("Compiling chronological block indexes...", "indigo");

            // Insert separator lines signifying sequential media blocks in Stage 3 workspace
            state.transcriptLines.push({
                id: `block-marker-${Date.now()}`,
                index: state.transcriptLines.length + 1,
                speaker: "SYSTEM INDEXER",
                text: "======= SEQUENTIAL MEDIA BATCH BLOCK #2 APPENDED Chronologically =======",
                type: "text",
                confidence: 1.0,
                hasSuggestion: false,
                duration: 0.0
            });

            state.transcriptLines.push({
                id: `seq-line-1`,
                index: state.transcriptLines.length + 1,
                speaker: "VANCE",
                text: "Thank you for joining us again for the afternoon session, Dr. Leifer.",
                type: "Q",
                confidence: 0.99,
                hasSuggestion: false,
                duration: 4.5
            });

            state.transcriptLines.push({
                id: `seq-line-2`,
                index: state.transcriptLines.length + 1,
                speaker: "LEIFER",
                text: "Of course. To clarify my earlier statement regarding the tumor margins...",
                type: "A",
                confidence: 0.91,
                hasSuggestion: false,
                duration: 5.0
            });

            compileAndRenderTranscript();
            renderSpeakersList();
        }

        // Hardware Microphone & Audio Analyser logic
        async function requestMicPermissions() {
            try {
                if (!state.audioContext) {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    state.micStream = stream;

                    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
                    state.audioContext = new AudioContextClass();
                    state.audioAnalyser = state.audioContext.createAnalyser();

                    const source = state.audioContext.createMediaStreamSource(stream);
                    source.connect(state.audioAnalyser);
                    state.audioAnalyser.fftSize = 32;
                }
            } catch (err) {
                showToast("Microphone capture disabled. Running in simulation mode.", "amber");
            }
        }

        function startZoomStreaming() {
            state.isStreaming = true;
            document.getElementById('btnStartStream').disabled = true;
            document.getElementById('btnStartStream').style.opacity = 0.5;
            document.getElementById('btnStopStream').disabled = false;
            document.getElementById('btnStopStream').style.opacity = 1.0;

            document.getElementById('liveStreamWaveGlow').classList.remove('opacity-0');
            document.getElementById('liveStreamWaveGlow').classList.add('opacity-100');
            document.getElementById('zoomStatusHeader').innerText = "Streaming live Zoom feed...";
            document.getElementById('zoomStatusHeader').className = "text-xs font-bold text-red-500 flex items-center gap-1.5 justify-center md:justify-start animate-pulse";
            document.getElementById('liveTimestamp').classList.remove('hidden');

            showToast("Deepgram Live streaming WebSocket active!", "red");
            addProvenanceRecord("Zoom WebSocket Stream", "Live streaming speech capture active.", "system");

            // Loop visualizer updates
            runAudioVisualizerAnimation();

            // Feed character-by-character transcript simulation
            runLiveTestimonySimulation();
        }

        function stopZoomStreaming() {
            state.isStreaming = false;
            document.getElementById('btnStartStream').disabled = false;
            document.getElementById('btnStartStream').style.opacity = 1.0;
            document.getElementById('btnStopStream').disabled = true;
            document.getElementById('btnStopStream').style.opacity = 0.5;

            document.getElementById('liveStreamWaveGlow').classList.add('opacity-0');
            document.getElementById('zoomStatusHeader').innerText = "Stream Disconnected";
            document.getElementById('zoomStatusHeader').className = "text-xs font-bold text-slate-400";
            document.getElementById('liveTimestamp').classList.add('hidden');

            clearInterval(state.visualizerTimer);
            showToast("Live stream disconnected successfully.");
        }

        // SVG Visualizer movement simulation mapping to real microphone amplitude if available
        function runAudioVisualizerAnimation() {
            const visualizerBars = document.getElementById('visualizerBars');
            const dataArray = new Uint8Array(state.audioAnalyser ? state.audioAnalyser.frequencyBinCount : 16);

            state.visualizerTimer = setInterval(() => {
                let amplitude = 25;
                if (state.audioAnalyser) {
                    state.audioAnalyser.getByteFrequencyData(dataArray);
                    amplitude = dataArray.reduce((acc, v) => acc + v, 0) / dataArray.length;
                } else {
                    amplitude = 15 + Math.random() * 40; // Random fallback visualizer
                }

                // Adjust SVG paths based on mic frequency
                const scale = Math.max(10, Math.min(amplitude, 60));
                visualizerBars.setAttribute('d', `M50,${50 - scale/2} L50,${50 + scale/2} M35,${50 - scale/3} L35,${50 + scale/3} M65,${50 - scale/3} L65,${50 + scale/3}`);

                // Keep live timer active
                const date = new Date();
                document.getElementById('liveTimestamp').innerText = date.toLocaleTimeString();
            }, 100);
        }

        // Simulate character generation of continuous speech
        function runLiveTestimonySimulation() {
            const container = document.getElementById('liveStreamTextContainer');
            container.innerHTML = "";
            let wordIdx = 0;

            const liveSentences = [
                "VANCE: Please state your occupation, Doctor.",
                "LEIFER: I am a board-certified neurosurgeon at Houston Neurological.",
                "VANCE: And you reviewed the MRI scans of Ms. Sarah Jenkins?",
                "LEIFER: Yes. We identified a sizable acoustic neuroma."
            ];

            const simInterval = setInterval(() => {
                if (!state.isStreaming) {
                    clearInterval(simInterval);
                    return;
                }

                if (wordIdx < liveSentences.length) {
                    const p = document.createElement('p');
                    p.className = "border-l-2 border-red-500 pl-2 py-1 bg-slate-900/40 rounded transition-all";
                    p.innerHTML = `<span class="text-[9px] text-slate-500 block">${new Date().toLocaleTimeString()}</span> ${liveSentences[wordIdx]}`;
                    container.appendChild(p);
                    container.scrollTop = container.scrollHeight;

                    // Automatically append streaming line arrays into transcriptLines database
                    const speakerTextParts = liveSentences[wordIdx].split(": ");
                    const isVance = speakerTextParts[0].includes("VANCE");

                    state.transcriptLines.push({
                        id: `live-line-${state.liveTranscriptCounter}`,
                        index: state.transcriptLines.length + 1,
                        speaker: isVance ? "VANCE" : "LEIFER",
                        text: speakerTextParts[1],
                        type: isVance ? "Q" : "A",
                        confidence: 0.95,
                        hasSuggestion: false,
                        duration: 3.5
                    });
                    state.liveTranscriptCounter++;

                    compileAndRenderTranscript();
                    wordIdx++;
                } else {
                    clearInterval(simInterval);
                }
            }, 3000);
        }

        // Interactive Live Search Read-Back Engine
        function executeReadbackSearch(query) {
            state.liveSearchQuery = query.toLowerCase().trim();
            const resultsBox = document.getElementById('readBackResultsContainer');
            resultsBox.innerHTML = "";

            if (!state.liveSearchQuery) {
                resultsBox.innerHTML = `<p class="text-[10px] text-slate-500 text-center py-24 italic font-sans">No queries tracked yet. Search above to check historical arrays.</p>`;
                return;
            }

            // Loop lines matching query
            const matches = state.transcriptLines.filter(line => line.text.toLowerCase().includes(state.liveSearchQuery));

            if (matches.length === 0) {
                resultsBox.innerHTML = `<p class="text-[10px] text-slate-500 text-center py-12 italic">No matches found for "${query}"</p>`;
                return;
            }

            matches.forEach(match => {
                const item = document.createElement('div');
                item.className = "bg-slate-900 border border-slate-850 p-2 rounded-lg cursor-pointer hover:border-red-500 transition-all";
                item.setAttribute('onclick', `quickJumpToLine('${match.id}')`);
                item.innerHTML = `
                    <div class="flex items-center justify-between text-[9px] font-mono mb-1">
                        <span class="text-indigo-400 font-semibold">${match.speaker}</span>
                        <span class="text-slate-500">LINE ${match.index}</span>
                    </div>
                    <p class="text-[11px] text-slate-300 font-mono leading-relaxed truncate font-mono">"${match.text}"</p>
                `;
                resultsBox.appendChild(item);
            });
        }


window.addFilesToIngestionQueue = addFilesToIngestionQueue;
window.addSingleFileToQueue = addSingleFileToQueue;
window.moveQueueItem = moveQueueItem;
window.renderFileQueue = renderFileQueue;
window.removeFileFromQueue = removeFileFromQueue;
window.clearAllQueues = clearAllQueues;
window.testGainAndAudio = testGainAndAudio;
window.startSequentialIngestion = startSequentialIngestion;
window.appendChronologicalMockSegments = appendChronologicalMockSegments;
window.requestMicPermissions = requestMicPermissions;
window.startZoomStreaming = startZoomStreaming;
window.stopZoomStreaming = stopZoomStreaming;
window.runAudioVisualizerAnimation = runAudioVisualizerAnimation;
window.runLiveTestimonySimulation = runLiveTestimonySimulation;
window.executeReadbackSearch = executeReadbackSearch;
