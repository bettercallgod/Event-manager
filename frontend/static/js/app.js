// EventDiscovery AI - Frontend JavaScript

const API_BASE = '';
let sessionId = localStorage.getItem('chatSessionId') || null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeChat();
    initializeSearch();
    initializeCreateEvent();
    loadDiscoverEvents();
});

// Chat functionality
function initializeChat() {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addChatMessage('user', message);
        chatInput.value = '';
        
        // Show typing indicator
        showTypingIndicator();
        
        try {
            const response = await fetch(`${API_BASE}/api/chat/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    session_id: sessionId
                })
            });
            
            const data = await response.json();
            
            // Update session ID
            sessionId = data.session_id;
            localStorage.setItem('chatSessionId', sessionId);
            
            // Remove typing indicator
            removeTypingIndicator();
            
            // Add AI response
            addChatMessage('assistant', data.ai_response);
            
            // Show events if any
            if (data.events && data.events.length > 0) {
                showEventResults(data.events);
            }
            
        } catch (error) {
            removeTypingIndicator();
            addChatMessage('assistant', 'Sorry, I encountered an error. Please try again! 😅');
            console.error('Chat error:', error);
        }
    });
}

function addChatMessage(role, content) {
    const messagesContainer = document.getElementById('chat-messages');
    const isUser = role === 'user';
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex items-start space-x-3 chat-message';
    messageDiv.innerHTML = `
        <div class="w-8 h-8 rounded-full ${isUser ? 'bg-gray-600' : 'bg-gradient-to-r from-purple-600 to-pink-600'} flex items-center justify-center text-white text-sm flex-shrink-0">
            ${isUser ? '👤' : 'AI'}
        </div>
        <div class="${isUser ? 'bg-purple-600 text-white' : 'bg-white'} rounded-lg ${isUser ? 'rounded-tr-none' : 'rounded-tl-none'} px-4 py-3 shadow-sm max-w-lg">
            <p class="${isUser ? 'text-white' : 'text-gray-800'}">${escapeHtml(content)}</p>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chat-messages');
    const indicator = document.createElement('div');
    indicator.id = 'typing-indicator';
    indicator.className = 'flex items-start space-x-3 chat-message';
    indicator.innerHTML = `
        <div class="w-8 h-8 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 flex items-center justify-center text-white text-sm">AI</div>
        <div class="bg-white rounded-lg rounded-tl-none px-4 py-3 shadow-sm">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    messagesContainer.appendChild(indicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

function showEventResults(events) {
    const resultsSection = document.getElementById('event-results');
    const eventsGrid = document.getElementById('events-grid');
    
    eventsGrid.innerHTML = events.map(event => createEventCard(event)).join('');
    resultsSection.classList.remove('hidden');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function createEventCard(event) {
    const priceDisplay = event.is_free ? 'Free' : `$${event.price}`;
    const dateDisplay = event.start_time ? new Date(event.start_time).toLocaleDateString() : 'TBD';
    
    return `
        <div class="event-card bg-white rounded-xl shadow-md overflow-hidden border border-gray-100">
            <div class="h-40 bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center">
                <span class="text-6xl">🎉</span>
            </div>
            <div class="p-5">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-semibold px-2 py-1 bg-purple-100 text-purple-700 rounded-full uppercase">
                        ${event.category || 'Event'}
                    </span>
                    <span class="text-sm font-bold text-green-600">${priceDisplay}</span>
                </div>
                <h4 class="text-xl font-bold mb-2 text-gray-800">${escapeHtml(event.title)}</h4>
                <p class="text-gray-600 text-sm mb-3 line-clamp-2">${escapeHtml(event.ai_summary || event.description || '')}</p>
                <div class="flex items-center justify-between text-sm text-gray-500">
                    <span>📅 ${dateDisplay}</span>
                    <span>📍 ${event.city || 'Location TBD'}</span>
                </div>
            </div>
        </div>
    `;
}

// Search functionality
function initializeSearch() {
    const searchForm = document.getElementById('search-form');
    
    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = document.getElementById('search-input').value.trim();
        const category = document.getElementById('filter-category').value;
        const priceFilter = document.getElementById('filter-price').value;
        
        if (!query) return;
        
        await performSearch(query, category, priceFilter);
    });
}

async function performSearch(query, category = '', priceFilter = '') {
    const grid = document.getElementById('discover-events-grid');
    grid.innerHTML = '<div class="col-span-full text-center py-12"><div class="spinner mx-auto"></div><p class="mt-4 text-gray-600">Searching events...</p></div>';
    
    try {
        let url = `${API_BASE}/api/events/search?q=${encodeURIComponent(query)}&use_semantic=true`;
        if (category) url += `&category=${category}`;
        if (priceFilter === 'free') url += `&max_price=0`;
        if (priceFilter === 'low') url += `&max_price=20`;
        if (priceFilter === 'medium') url += `&max_price=50`;
        
        const response = await fetch(url);
        const events = await response.json();
        
        if (events.length === 0) {
            grid.innerHTML = '<div class="col-span-full text-center py-12"><p class="text-gray-600">No events found. Try a different search!</p></div>';
        } else {
            grid.innerHTML = events.map(event => createEventCard(event)).join('');
        }
    } catch (error) {
        console.error('Search error:', error);
        grid.innerHTML = '<div class="col-span-full text-center py-12"><p class="text-red-600">Error loading events. Please try again.</p></div>';
    }
}

async function loadDiscoverEvents() {
    const grid = document.getElementById('discover-events-grid');
    
    try {
        const response = await fetch(`${API_BASE}/api/events/recommendations?limit=9`);
        const events = await response.json();
        
        if (events.length > 0) {
            grid.innerHTML = events.map(event => createEventCard(event)).join('');
        } else {
            grid.innerHTML = '<div class="col-span-full text-center py-12"><p class="text-gray-600">No events available yet. Be the first to create one!</p></div>';
        }
    } catch (error) {
        console.error('Load events error:', error);
        grid.innerHTML = '<div class="col-span-full text-center py-12"><p class="text-gray-600">Unable to load events. Check back soon!</p></div>';
    }
}

// Create event functionality
function initializeCreateEvent() {
    const createForm = document.getElementById('create-event-form');
    
    createForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const description = document.getElementById('event-description').value.trim();
        
        if (!description) return;
        
        const submitBtn = createForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Creating...';
        submitBtn.disabled = true;
        
        try {
            const response = await fetch(`${API_BASE}/api/events/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    conversation_text: description
                })
            });
            
            const event = await response.json();
            
            const resultDiv = document.getElementById('create-result');
            resultDiv.innerHTML = `
                <div class="bg-green-50 border border-green-200 rounded-lg p-6">
                    <h4 class="text-xl font-bold text-green-800 mb-2">🎉 Event Created Successfully!</h4>
                    <p class="text-green-700 mb-4"><strong>${escapeHtml(event.title)}</strong></p>
                    <p class="text-gray-600 text-sm mb-4">${escapeHtml(event.ai_summary || event.description || '')}</p>
                    <button onclick="document.getElementById('create-result').innerHTML=''; document.getElementById('event-description').value='';" class="text-green-600 hover:text-green-800 font-semibold">
                        Create Another Event →
                    </button>
                </div>
            `;
            resultDiv.classList.remove('hidden');
            
            // Clear form
            document.getElementById('event-description').value = '';
            
        } catch (error) {
            console.error('Create event error:', error);
            alert('Error creating event. Please try again!');
        } finally {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    });
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
