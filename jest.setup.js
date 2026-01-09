require('jest-localstorage-mock');
require('@testing-library/jest-dom');

global.bootstrap = {
  Modal: jest.fn().mockImplementation(() => ({
    show: jest.fn(),
    hide: jest.fn(),
  })),
  Tooltip: jest.fn().mockImplementation(() => ({
    hide: jest.fn(),
  })),
  Toast: jest.fn().mockImplementation(() => ({
    show: jest.fn(),
    hide: jest.fn(),
  })),
};

bootstrap.Tooltip.getInstance = jest.fn();

Object.defineProperty(document, 'cookie', {
  writable: true,
  value: '',
});
