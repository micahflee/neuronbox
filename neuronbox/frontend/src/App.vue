<template>
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-3">
                <div class="d-flex justify-content-center mb-4">
                    <span class="title">NeuronBox</span>
                </div>
            </div>
            <div class="col-md-9 main-content">
                <router-view></router-view>
            </div>
        </div>
    </div>
</template>

<script setup>
</script>

<style>
.title {
    font-size: 2rem;
    font-weight: bold;
}

.main-content {
    padding: 1rem;
}

a {
    color: #007bff;
    text-decoration: none;
}

a:hover {
    color: #0056b3;
    text-decoration: underline;
}
</style>