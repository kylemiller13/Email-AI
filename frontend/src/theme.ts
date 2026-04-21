import { extendTheme, type ThemeConfig } from '@chakra-ui/react';

const config: ThemeConfig = {
  initialColorMode: 'dark',
  useSystemColorMode: false,
};

const theme = extendTheme({
  config,
  fonts: {
    body: '"Inter", sans-serif',
    heading: '"Inter", sans-serif',
  },
  colors: {
    brand: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
    },
    semantic: {
      critical: '#ef4444', // Red for critical/phishing
      warning: '#f97316',  // Orange for warnings
      caution: '#eab308',  // Yellow for caution
      safe: '#10b981',     // Green for safe
    },
  },
  components: {
    Button: {
      baseStyle: {
        fontWeight: 600,
      },
      variants: {
        solid: {
          _dark: {
            bg: 'brand.600',
            color: 'white',
            _hover: {
              bg: 'brand.700',
            },
          },
        },
      },
      defaultProps: {
        colorScheme: 'blue',
      },
    },
    Input: {
      baseStyle: {
        field: {
          fontFamily: 'body',
        },
      },
    },
  },
  styles: {
    global: {
      body: {
        bg: 'gray.900',
        color: 'gray.100',
      },
    },
  },
});

export default theme;
