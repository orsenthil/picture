/**
 * Jest setup file for browser extension tests
 * This file runs before each test file
 */

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

global.localStorage = localStorageMock;

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    origin: 'http://localhost:8000',
    href: 'http://localhost:8000/',
  },
  writable: true,
});

// Mock fetch globally
global.fetch = jest.fn();

// Reset mocks before each test
beforeEach(() => {
  localStorage.clear();
  fetch.mockClear();
  document.body.innerHTML = '';
});

