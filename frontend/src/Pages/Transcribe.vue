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
                    <option value="small">Small (244MB download, needs ~2GB RAM)</option>
                    <option value="medium">Medium (789MB download, needs ~5GB RAM)</option>
                    <option value="large">Large (1.5GB download, needs ~10GB RAM)</option>
                </select>
            </div>

            <button type="submit" class="btn btn-primary">Transcribe</button>
        </form>

        <Error v-if="showError" :message="errorMessage" @close="showError = false"></Error>
    </div>
</template>
  
<script setup>
import { ref } from 'vue';
import { invoke } from '@tauri-apps/api/tauri';
import axios from 'axios';

import Error from '../Components/Error.vue';

const showError = ref(false);
const errorMessage = ref('');

const formData = ref({
    filename: '',
    model: 'small'
});

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
            errorMessage.value = data.error;
            showError.value = true;
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