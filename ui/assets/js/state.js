        const state = {
            currentStage: 1,
            workspaceMode: 'edit', // edit, suggestions, audio, formatting
            canvasTheme: 'dark', // dark, word (MS Word Mockup)

            // Texas UFM Mandatory Schema Mapping (Binds directly to verified input UI)
            caseInfo: {
                cause: "",
                caption: "SARAH JENKINS vs. NEXUS PHARMA INC.",
                court: "",
                county: "",
                state: "Texas",
                deponent: "",
                date: "",
                startTime: "",
                endTime: "",
                address: "",
                csrName: "",
                csrLicense: "",
                firmReg: "",
                csrCertExp: "",
                custodialName: "",
                requestingParty: "",
                strictLineLock: true,
                signature: "",
                certified: false
            },

            // Multiple Files Processing Sequence Queue State
            fileQueue: [],
            isQueueProcessing: false,
            elapsedProcessTime: 0,
            elapsedTimerInterval: null,

            // Sequence of transcript lines containing alignments, confidence arrays, and metadata
            transcriptLines: [
                { id: "line-1", index: 1, speaker: "VANCE", text: "State your full name and credentials for the record, please.", type: "Q", confidence: 0.98, hasSuggestion: false, duration: 4.2 },
                { id: "line-2", index: 2, speaker: "LEIFER", text: "Dr. Donald Leifer. I am a board-certified neurosurgeon with Houston Neurological.", type: "A", confidence: 0.94, hasSuggestion: true, suggestion: { word: "Leifer", original: "lifer", replacement: "Leifer", source: "NOD File Alignment", confidence: 0.97 }, duration: 5.5 },
                { id: "line-3", index: 3, speaker: "VANCE", text: "And did you have occasion to review the MRI scans for Ms. Sarah Jenkins?", type: "Q", confidence: 0.99, hasSuggestion: false, duration: 4.0 },
                { id: "line-4", index: 4, speaker: "LEIFER", text: "Yes, we took detailed brain scans and identified an acoustic neuroma.", type: "A", confidence: 0.72, hasSuggestion: true, suggestion: { word: "acoustic neuroma", original: "a coostik new roma", replacement: "acoustic neuroma", source: "NOD Medical Dictionary", confidence: 0.94 }, duration: 6.1 },
                { id: "line-5", index: 5, speaker: "VANCE", text: "Let the record reflect that MRI scans are now marked as Exhibit 1 for identification.", type: "Q", confidence: 0.97, hasSuggestion: false, duration: 5.0, exhibit: 1 },
                { id: "line-6", index: 6, speaker: "VANCE", text: "Can you confirm the dimensions of the mass found during that scan, Doctor?", type: "Q", confidence: 0.96, hasSuggestion: false, duration: 4.5 },
                { id: "line-7", index: 7, speaker: "LEIFER", text: "It was approximately, um, 2.4 centimeters on the largest axis.", type: "A", confidence: 0.81, hasSuggestion: true, suggestion: { word: "um", original: "um", replacement: "", type: "filler", source: "Filler deletion Suggestion", confidence: 0.99 }, duration: 4.8 },
                { id: "line-8", index: 8, speaker: "VANCE", text: "And was that mass compromising the adjacent nerve structures?", type: "Q", confidence: 0.98, hasSuggestion: false, duration: 3.8 },
                { id: "line-9", index: 9, speaker: "LEIFER", text: "Yes. It was compressing the seventh cranial nerve pathway.", type: "A", confidence: 0.95, hasSuggestion: false, duration: 5.2 }
            ],
            exhibits: [
                { id: "ex-1", num: 1, title: "MRI Imaging Scans - Left Frontal Lobe", page: 1, line: 5, attorney: "Mr. Richard Vance" },
                { id: "ex-2", num: 2, title: "Neurosurgeon Practice Certification", page: 1, line: 9, attorney: "Mr. Richard Vance" }
            ],
            correctionsMemory: [
                { original: "doctor lifer", replacement: "Doctor Leifer", scope: "global" },
                { original: "nexus farma", replacement: "Nexus Pharma", scope: "case" }
            ],
            provenance: [
                { title: "Deepgram Transcribe", text: "Raw transcription engine connected successfully.", timestamp: "10:24 AM", type: "system" },
                { title: "NOD dictionary seed", text: "Extracted Doctor Leifer as primary deponent.", timestamp: "10:24 AM", type: "ai" }
            ],
            activePlayback: false,
            playbackInterval: null,
            playbackLineIdx: 0,
            playbackSpeed: 1.0,
            focusedLineId: "line-1",

            // Audio input streaming configuration
            isStreaming: false,
            audioContext: null,
            audioAnalyser: null,
            micStream: null,
            visualizerTimer: null,
            liveTranscriptCounter: 10,
            liveSearchQuery: ""
        };
window.state = state;
