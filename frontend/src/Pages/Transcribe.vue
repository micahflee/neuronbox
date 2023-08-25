<template>
    <div>
        <h1>Transcribe Audio</h1>
        <button @click="openFileDialog">Browse File</button>
    </div>
</template>
  
<script setup>
import { invoke } from '@tauri-apps/api/tauri'

async function openFileDialog() {
    invoke('select_file').then(response => {
        if (response.file_path) {
            console.log("File path selected:", response.file_path);
        } else {
            console.log("No file was selected.");
        }
    });
}
</script>

<style scoped></style>
  