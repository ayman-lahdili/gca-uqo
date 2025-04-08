import { reactive } from 'vue';

// Create a reactive object to hold the shared state and methods to modify it
export const sharedSelectState = reactive({
    selectedValue: localStorage.getItem('selectedTrimestre') === undefined ? null : Number(localStorage.getItem('selectedTrimestre')),
    trimestreOptions: JSON.parse(localStorage.getItem('trimestreOptions')) || [],

    // Method to update the shared state
    setSelectedValue(newValue) {
        this.selectedValue = newValue; // 'this' refers to the reactive object itself
        localStorage.setItem('selectedTrimestre', newValue);
    },

    // Method to update the trimestre options
    updateTrimestreOptions(newTrimestre) {
        if (!this.trimestreOptions.includes(newTrimestre)) {
            this.trimestreOptions.push(newTrimestre);
            localStorage.setItem('trimestreOptions', JSON.stringify(this.trimestreOptions));
        }
    }
});
