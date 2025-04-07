import { reactive } from 'vue';

// Create a reactive object to hold the shared state and methods to modify it
export const sharedSelectState = reactive({
    selectedValue: localStorage.getItem('selectedTrimestre') === undefined ? null : Number(localStorage.getItem('selectedTrimestre')),

    // Method to update the shared state
    setSelectedValue(newValue) {
        this.selectedValue = newValue; // 'this' refers to the reactive object itself
    }
});
