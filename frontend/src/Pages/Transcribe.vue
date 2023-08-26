<template>
    <div>
        <h1>Transcribe Audio</h1>
        <button @click="openFileDialog">Browse File</button>
    </div>
</template>
  
<script setup>
import { invoke } from '@tauri-apps/api/tauri'

async function openFileDialog() {
    invoke('select_file').then(filename => {
        if (filename) {
            console.log("File path selected:", filename);
        } else {
            console.log("No file was selected.");
        }
    });
}
</script>

<style scoped></style>
  