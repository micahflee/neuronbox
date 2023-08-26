<template>
    <div class="container">
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
                    <option value="small">Small (461MB download, requires ~2GB RAM)</option>
                    <option value="medium">Medium (789MB download, requires ~5GB RAM)</option>
                    <option value="large">Large (1.5GB download, requires ~10GB RAM)</option>
                </select>
            </div>

            <button type="submit" class="btn btn-primary" :disabled="isSubmitDisabled">Transcribe</button>
        </form>
    </div>
</template>
  
<script setup>
import { ref, computed } from 'vue';
import { invoke } from '@tauri-apps/api/tauri';
import axios from 'axios';

const formData = ref({
    filename: '',
    model: 'small'
});

const isSubmitDisabled = computed(() => !formData.value.filename);

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
    try {
        const response = await axios.post('http://127.0.0.1:52014/transcribe', formData.value);
        const data = response.data;
        if (data.error) {
            invoke('message_dialog', {
                title: 'Transcription Error',
                message: data.error,
                kind: 'error'
            });
        } else {
            // Handle successful response
            console.log("Successful response received.", data);
        }
    } catch (error) {
        console.error("There was an issue submitting the form:", error);
    }
}
</script>

<style scoped></style>