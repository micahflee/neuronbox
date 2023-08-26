<template>
    <div class="container">
        <div v-if="isLoading" class="d-flex justify-content-center align-items-center flex-column">
            <img src="/assets/waiting-on-ai.gif" alt="Loading..." class="mb-4 loading">
            <p>Waiting on the AI to transcribe the audio...</p>
        </div>
        <div v-if="!isLoading && !transcriptionResult">
            <h1 class="mb-4">Transcribe Audio</h1>
            <p class="mb-4">Choose an audio file on your computer to transcribe it.</p>

            <form @submit.prevent="submitForm">
                <div class="mb-3">
                    <label for="filename" class="form-label">Filename:</label>
                    <div class="input-group">
                        <input type="text" id="filename" v-model="formData.filename" class="form-control" disabled />
                        <button type="button" @click="openFileDialog" class="btn btn-outline-secondary">Browse</button>
                    </div>
                </div>

                <div class="mb-3">
                    <label for="model" class="form-label">Model:</label>
                    <select id="model" v-model="formData.model" class="form-select">
                        <option v-for="model in models.transcribe" :key="model.name" :value="model.name">
                            {{ model.description }}
                        </option>
                    </select>
                </div>

                <button type="submit" class="btn btn-primary" :disabled="isSubmitDisabled">Transcribe</button>
            </form>
        </div>
        <div v-if="transcriptionResult">
            <h1 class="mb-4">Transcription Results</h1>
            <p class="small text-muted">
                Filename: {{ formData.filename }}<br />
                Time elapsed: {{ formattedTimeElapsed }}
            </p>
            <p>{{ transcriptionResult }}</p>
        </div>

    </div>
</template>
  
<script setup>
import { ref, computed, onMounted } from 'vue';
import { invoke } from '@tauri-apps/api/tauri';
import axios from 'axios';

import { API_URL } from '../config';

const isLoading = ref(false);
const transcriptionResult = ref(null);
const transcriptionTimeElapsed = ref(null);

const formattedTimeElapsed = computed(() => {
    const minutes = Math.floor(transcriptionTimeElapsed.value / 60);
    const seconds = Math.round(transcriptionTimeElapsed.value % 60);
    return `${minutes} minute(s) and ${seconds} second(s)`;
});

const formData = ref({
    filename: '',
    model: 'small'
});

const models = ref({
    transcribe: []
});

const isSubmitDisabled = computed(() => !formData.value.filename);

async function loadModels() {
    try {
        const response = await axios.get(`${API_URL}/models`);
        models.value = response.data.models;
    } catch (error) {
        console.error("Failed to load models:", error);
    }
}

onMounted(loadModels);

async function openFileDialog() {
    invoke('select_file').then(filename => {
        if (filename) {
            formData.value.filename = filename;
            console.log("File path selected:", filename);
        } else {
            console.log("No file was selected.");
        }
    });
}

async function submitForm() {
    isLoading.value = true;

    try {
        const response = await axios.post(`${API_URL}/transcribe`, formData.value, { timeout: 1200000 });
        if (!response.data.success) {
            invoke('message_dialog', {
                title: 'Transcription error',
                message: response.data.error,
                kind: 'error'
            });
        } else {
            transcriptionResult.value = response.data.result;
            transcriptionTimeElapsed.value = response.data.time_elapsed;
        }
    } catch (error) {
        console.error("There was an issue submitting the form:", error);
        invoke('message_dialog', {
            title: 'Transcription error',
            message: error,
            kind: 'error'
        });
    } finally {
        isLoading.value = false;
    }
}

</script>

<style scoped>
.loading {
    border-radius: 50vw;
}
</style>
