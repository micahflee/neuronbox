<template>
    <div class="row mb-3">
        <div class="col-md-4">
            <p class="model-name">
                {{ props.model.name }}
            </p>
        </div>
        <div class="col-md-4">
            <p>{{ props.model.description }}</p>
        </div>
        <div class="col-md-2">
            <div v-if="isDownloading">
                <div class="progress">
                    <div class="progress-bar" role="progressbar" :style="{ width: downloadProgress + '%' }"
                        :aria-valuenow="downloadProgress" aria-valuemin="0" aria-valuemax="100">
                        {{ downloadProgress.toFixed(0) }}%
                    </div>
                </div>
            </div>
            <p v-else-if="model.downloaded" class="small text-muted">Downloaded</p>
            <p v-else class="small text-muted">Not downloaded</p>
        </div>
        <div class="col-md-2">
            <button v-if="model.downloaded" @click="deleteModel()" class="btn btn-danger">Delete</button>
            <button v-else-if="isDownloading" @click="cancelDownload()" class="btn btn-warning">Cancel</button>
            <button v-else @click="downloadModel()" class="btn btn-primary">Download</button>
        </div>
    </div>
</template>

  
<script setup>
import { ref, defineEmits } from 'vue'
import axios from 'axios';
import { invoke } from '@tauri-apps/api/tauri';

import { API_URL } from '../config';

const props = defineProps({
    featureName: String,
    model: Object,
})

const emit = defineEmits(['refresh-models']);

const isDownloading = ref(false);
const downloadProgress = ref(0);
const eventSource = ref(null);

const deleteModel = async () => {
    try {
        const response = await axios.post(`${API_URL}/models/delete`, { feature: props.featureName, model: props.model.name });
        if (!response.data.success) {
            invoke('message_dialog', {
                title: 'Delete error',
                message: response.data.error,
                kind: 'error'
            });
        }

        // Refresh models after deletion
        emit('refresh-models');
    } catch (error) {
        invoke('message_dialog', {
            title: 'Error deleting model',
            message: error.message,
            kind: 'error'
        });
        console.error("Error deleting model:", error);
    }
}

const downloadModel = async () => {
    try {
        isDownloading.value = true;
        downloadProgress.value = 0;

        // Initialize SSE
        eventSource.value = new EventSource(`${API_URL}/download-progress/${props.featureName}/${props.modelName}`);
        eventSource.value.onmessage = function (event) {
            const progress = parseFloat(event.data);
            downloadProgress.value = progress;
            if (progress === 100) {
                eventSource.value.close();
                isDownloading.value = false;
                props.model.downloaded = true;
            }
        };

        // Handle errors (optional)
        eventSource.value.onerror = function (error) {
            invoke('message_dialog', {
                title: 'EventSource failed',
                message: error.message,
                kind: 'error'
            });
            console.error("EventSource failed:", error);
            eventSource.value.close();

            isDownloading.value = false;
            downloadProgress.value = 0;
        };

        // Start download
        const response = await axios.post(`${API_URL}/models/download`, { feature: props.featureName, model: props.model.name }, { timeout: 1200000 });
        if (!response.data.success) {
            invoke('message_dialog', {
                title: 'Download error',
                message: response.data.error,
                kind: 'error'
            });

            isDownloading.value = false;
            downloadProgress.value = 0;
        } else {
            // Refresh models after download
            emit('refresh-models');
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

const cancelDownload = async () => {
    try {
        const response = await axios.post(`${API_URL}/models/cancel-download`, { feature: props.featureName, model: props.model.name });
        if (!response.data.success) {
            invoke('message_dialog', {
                title: 'Cancel download error',
                message: response.data.error,
                kind: 'error'
            });
        }

        isDownloading.value = false;
        downloadProgress.value = 0;

        if (eventSource.value) {
            eventSource.value.close();
            eventSource.value = null;
        }
    } catch (error) {
        invoke('message_dialog', {
            title: 'Error canceling download',
            message: error.message,
            kind: 'error'
        });
        console.error("Error canceling download:", error);

        isDownloading.value = false;
        downloadProgress.value = 0;
    }
}
</script>
  
<style scoped>
.model-name {
    font-weight: bold;
    padding-left: 1rem;
}

.progress-bar {
    padding: 10px;
}
</style>
