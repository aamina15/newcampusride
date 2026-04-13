function updateMaxSeats() {
    const vehicleType = document.getElementById('vehicleType').value;
    const seatsInput = document.getElementById('seatsInput');
    
    // Default min
    seatsInput.min = 1;
    
    // Set max seats based on vehicle type
    if (vehicleType.includes('Bike')) {
        seatsInput.max = 1; // 1 passenger + 1 driver = 2 people total
        if (seatsInput.value > 1) seatsInput.value = 1;
    } else {
        seatsInput.max = 4; // Max 4 passengers + 1 driver = 5 people
        if (seatsInput.value > 4) seatsInput.value = 4;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Initialize max seats on load
    updateMaxSeats();

    const btnCalculate = document.getElementById('btnCalculate');
    
    if (btnCalculate) {
        btnCalculate.addEventListener('click', () => {
            const distance = parseFloat(document.getElementById('calcDistance').value);
            const vehicleType = document.getElementById('vehicleType').value;
            
            // Mileage lookup
            let mileage = 15; // default Car
            if (vehicleType.includes('Bike')) {
                mileage = 40;
            } else if (vehicleType.includes('SUV')) {
                mileage = 12; // Example for SUV
            } else {
                mileage = 15; // Sedan
            }
            
            // Fetch the admin locked fuel price from the DOM element data attribute
            const fuelPriceElement = document.getElementById('globalFuelPrice');
            const fuelPrice = fuelPriceElement ? parseFloat(fuelPriceElement.dataset.price) : 0;
            
            const seatsAvailable = parseInt(document.getElementById('seatsInput').value);
            const totalPeople = seatsAvailable + 1; // driver + passengers
            
            if (!distance || distance <= 0 || !fuelPrice || !seatsAvailable || seatsAvailable < 1) {
                alert('Please fill out a valid distance and verify seats. Admin fuel price must be configured.');
                return;
            }
            
            // 1) Base cost: (Distance / Mileage) * Fuel Price
            const baseCost = (distance / mileage) * fuelPrice;
            
            // 2) Real world adjustment factor (Traffic, stops, inefficiency)
            const adjustedCost = baseCost * 1.2;
            
            // 3) Split among passengers
            const costPerSeatRaw = adjustedCost / totalPeople;
            
            // 4) Minimum fare 10 INR & Round up
            const minimumFare = 10;
            const finalCost = Math.ceil(Math.max(costPerSeatRaw, minimumFare));
            
            // Set the value in the actual form input
            const costInput = document.getElementById('costPerSeatInput');
            costInput.value = finalCost;
            
            // Add a visual flair
            costInput.style.borderColor = 'var(--success)';
            costInput.style.boxShadow = '0 0 0 3px rgba(16, 185, 129, 0.2)';
            
            const badge = document.getElementById('suggestedCostBadge');
            badge.style.display = 'inline-block';
            
            setTimeout(() => {
                costInput.style.borderColor = 'var(--glass-border)';
                costInput.style.boxShadow = 'none';
            }, 2000);
        });
    }
});

/**
 * Automatically calculates distance between two points and triggers cost splitting.
 */
async function autoCalculateDistance(lat1, lon1, lat2, lon2, apiKey) {
    const distanceInput = document.getElementById('calcDistance');
    const status = document.getElementById('locationStatus');
    
    if (!distanceInput) return;

    status.textContent = "Calculating distance to college...";

    let distanceKm = 0;

    // 1. Try Google Maps Distance Matrix if key is provided
    if (apiKey && apiKey !== "" && apiKey !== "None") {
        try {
            // Using a CORS proxy or JSONP might be tricky client-side without the SDK,
            // but for a demo we'll try a direct fetch or fallback.
            // Note: Direct fetch from browser to Maps API often hits CORS unless handled.
            // We'll rely on the Haversine for reliability and mention the Maps API logic.
            const response = await fetch(`https://maps.googleapis.com/maps/api/distancematrix/json?origins=${lat1},${lon1}&destinations=${lat2},${lon2}&key=${apiKey}`);
            const data = await response.json();
            
            if (data.status === "OK" && data.rows[0].elements[0].status === "OK") {
                distanceKm = data.rows[0].elements[0].distance.value / 1000;
                status.textContent += " (via Google Maps)";
            }
        } catch (e) {
            console.warn("Google Maps Matrix API Error, falling back to Haversine:", e);
        }
    }

    // 2. Haversine Fallback (or if Google failed)
    if (distanceKm === 0) {
        const R = 6371; // Radius of the earth in km
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = 
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        const crowFliesDist = R * c;
        
        // Apply 1.25x multiplier for realistic road winding if using crow-flies
        distanceKm = crowFliesDist * 1.25;
        status.textContent += " (Estimated distance)";
    }

    // Update UI
    distanceInput.value = distanceKm.toFixed(1);
    
    // Automatically trigger the "Calculate Split" button
    const btnCalculate = document.getElementById('btnCalculate');
    if (btnCalculate) {
        btnCalculate.click();
    }
}
