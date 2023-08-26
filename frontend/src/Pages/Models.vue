<template>
    <div class="container">
        <h1 class="mb-4">Models</h1>
        <p class="mb-4">
            All of my smarts come from open source AI models. These models can get big so I'm not packaged with them. Since
            I operate entirely on your computer, you'll need to download the models that you want to use.
        </p>

        <!-- Transcribe Audio Section -->
        <div class="card mb-4">
            <div class="card-header">Transcribe Audio</div>
            <div class="card-body">
                <p>
                    I transcribe audio using OpenAI's open source neural network called <a
                        href="https://openai.com/research/whisper" target="_blank">Whisper</a>.
                    You have a choice of using different sized models
                    (<a href="https://github.com/openai/whisper/blob/main/model-card.md" target="_blank">learn more</a>
                    about the differences between these models). The larger models require significantly more disk space and
                    RAM compared to the smaller models.
                </p>

                <!-- Loop over each model -->
                <div v-for="model in transcribeModels" :key="model.name" class="row mb-3">
                    <!-- Model Name -->
                    <div class="col-md-2">
                        <h5>{{ model.name }}</h5>
                    </div>
                    <!-- Model Description -->
                    <div class="col-md-6">
                        <p>{{ model.description }}</p>
                    </div>
                    <!-- Download Progress and Status -->
                    <div class="col-md-2">
                        <div v-if="model.downloading">
                            <!-- Progress Bar -->
                            <div class="progress">
                                <div class="progress-bar" role="progressbar" :style="{ width: model.progress + '%' }"
                                    :aria-valuenow="model.progress" aria-valuemin="0" aria-valuemax="100">
                                    {{ model.progress.toFixed(0) }}%
                                </div>
                            </div>
                        </div>
                        <p v-else-if="model.downloaded">Downloaded</p>
                        <p v-else>Not downloaded</p>
                    </div>
                    <!-- Action Buttons -->
                    <div class="col-md-2">
                        <button v-if="model.downloaded" @click="deleteModel('transcribe', model.name)"
                            class="btn btn-danger">Delete</button>
                        <button v-else-if="model.downloading" @click="cancelDownload('transcribe', model.name)"
                            class="btn btn-warning">Cancel</button>
                        <button v-else @click="downloadModel('transcribe', model.name)"
                            class="btn btn-primary">Download</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
  
<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { invoke } from '@tauri-apps/api/tauri';

import { API_URL } from '../config';

const transcribeModels = ref([]);

onMounted(async () => {
    try {
        const response = await axios.get(`${API_URL}/models`);
        transcribeModels.value = response.data.models.transcribe;
    } catch (error) {
        invoke('message_dialog', {
            title: 'Error fetching models',
            message: error.message,
            kind: 'error'
        });
        console.error("Error fetching models:", error);
    }
});

const deleteModel = async (featureName, modelName) => {
    try {
        const response = await axios.post(`${API_URL}/models/delete`, { feature: featureName, model: modelName });
        if (!response.data.success) {
            invoke('message_dialog', {
                title: 'Delete error',
                message: response.data.error,
                kind: 'error'
            });
        }

        // Refresh models after deletion
        const response2 = await axios.get(`${API_URL}/models`);
        transcribeModels.value = response2.data.models.transcribe;
    } catch (error) {
        invoke('message_dialog', {
            title: 'Error deleting model',
            message: error.message,
            kind: 'error'
        });
        console.error("Error deleting model:", error);
    }
}

const downloadModel = async (featureName, modelName) => {
    try {
        const model = transcribeModels.value.find(m => m.name === modelName);
        model.downloading = true;
        model.progress = 0;

        // Initialize SSE
        model.eventSource = new EventSource(`${API_URL}/download-progress/${featureName}/${modelName}`);
        model.eventSource.onmessage = function (event) {
            const progress = parseFloat(event.data);
            model.progress = progress;
            if (progress === 100) {
                model.eventSource.close();
                model.downloading = false;
                model.downloaded = true;
            }
        };

        // Handle errors (optional)
        model.eventSource.onerror = function (error) {
            invoke('message_dialog', {
                title: 'EventSource failed',
                message: error.message,
                kind: 'error'
            });
            console.error("EventSource failed:", error);
            model.eventSource.close();

            const model = transcribeModels.value.find(m => m.name === modelName);
            model.downloading = false;
            model.progress = 0;
        };

        // Start download
        const response = await axios.post(`${API_URL}/models/download`, { feature: featureName, model: modelName }, { timeout: 1200000 });
        if (!response.data.success) {
            invoke('message_dialog', {
                title: 'Download error',
                message: response.data.error,
                kind: 'error'
            });

            const model = transcribeModels.value.find(m => m.name === modelName);
            model.downloading = false;
            model.progress = 0;
        } else {
            // Refresh models after download
            const response2 = await axios.get(`${API_URL}/models`);
            transcribeModels.value = response2.data.models.transcribe;
        }
    } catch (error) {
        invoke('message_dialog', {
            title: 'Error downloading model',
            message: error.message,
            kind: 'error'
        });
        console.error("Error downloading model:", error);
    }
}

const cancelDownload = async (featureName, modelName) => {
    try {
        const response = await axios.post(`${API_URL}/models/cancel-download`, { feature: featureName, model: modelName });
        if (!response.data.success) {
            invoke('message_dialog', {
                title: 'Cancel download error',
                message: response.data.error,
                kind: 'error'
            });
        }

        const model = transcribeModels.value.find(m => m.name === modelName);
        model.downloading = false;
        model.progress = 0;

        if (model.eventSource) {
            model.eventSource.close();
            model.eventSource = null;
        }
    } catch (error) {
        invoke('message_dialog', {
            title: 'Error canceling download',
            message: error.message,
            kind: 'error'
        });
        console.error("Error canceling download:", error);

        const model = transcribeModels.value.find(m => m.name === modelName);
        model.downloading = false;
        model.progress = 0;
    }
}
</script>
  
<style scoped>
.progress-bar {
    padding: 10px;
}
</style>
