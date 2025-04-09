// sharedSelectedState.js
import { reactive, watch } from 'vue';

// Function to safely get and parse from localStorage
function getFromLocalStorage(key, defaultValue) {
    const storedValue = localStorage.getItem(key);
    if (storedValue === null || storedValue === undefined) {
        return defaultValue;
    }
    try {
        // For options, parse JSON; for selectedValue, parse as Number
        if (key === 'trimestreOptions') {
            return JSON.parse(storedValue) || defaultValue;
        }
        if (key === 'selectedTrimestre') {
            const num = Number(storedValue);
            return isNaN(num) ? defaultValue : num;
        }
        return storedValue; // Should not happen for these keys
    } catch (error) {
        console.error(`Error parsing localStorage key "${key}":`, error);
        return defaultValue;
    }
}

export const sharedSelectState = reactive({
    // Use the helper function for safe initialization
    selectedValue: getFromLocalStorage('selectedTrimestre', null),
    trimestreOptions: getFromLocalStorage('trimestreOptions', []),

    setSelectedValue(newValue) {
        const numericValue = newValue === null || newValue === undefined ? null : Number(newValue);
        console.log('selectedTrimestre', this.selectedValue, numericValue);
        if (this.selectedValue !== numericValue) {
            this.selectedValue = numericValue;
            // Persist null/undefined as empty string or handle appropriately
            localStorage.setItem('selectedTrimestre', numericValue === null ? '' : String(numericValue));
            console.log('Shared state selectedValue updated:', this.selectedValue);
        } else {
            localStorage.setItem('selectedTrimestre', numericValue === null ? '' : String(numericValue));
        }
    },

    updateTrimestreOptions(newTrimestre) {
        const numericTrimestre = Number(newTrimestre); // Ensure it's a number
        if (!isNaN(numericTrimestre) && !this.trimestreOptions.includes(numericTrimestre)) {
            // Keep options sorted if desired (optional)
            this.trimestreOptions.push(numericTrimestre);
            this.trimestreOptions.sort((a, b) => b - a); // Example: sort descending
            localStorage.setItem('trimestreOptions', JSON.stringify(this.trimestreOptions));
            console.log('Shared state trimestreOptions updated:', this.trimestreOptions);

            // Optional: Check if selectedValue needs initialization or validation
            if (this.selectedValue === null && this.trimestreOptions.length > 0) {
                // If nothing is selected, select the newly added one or the first one
                this.setSelectedValue(numericTrimestre);
            }
        }
    },

    // Method to ensure selectedValue is valid within the options
    validateSelection() {
        if (this.selectedValue !== null && !this.trimestreOptions.includes(this.selectedValue)) {
            console.warn(`Selected value ${this.selectedValue} not in options. Resetting.`);
            // Reset to the first available option, or null if none exist
            this.setSelectedValue(this.trimestreOptions.length > 0 ? this.trimestreOptions[0] : null);
        } else if (this.selectedValue === null && this.trimestreOptions.length > 0) {
            // If null but options exist, select the first one
            this.setSelectedValue(this.trimestreOptions[0]);
        }
    }
});

// Watch for changes in options and validate the current selection
watch(
    () => [...sharedSelectState.trimestreOptions],
    () => {
        sharedSelectState.validateSelection();
    },
    { deep: true }
);

// Initial validation on load
sharedSelectState.validateSelection();
