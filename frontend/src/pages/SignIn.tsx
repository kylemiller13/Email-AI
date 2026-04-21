import { useEffect, useState } from 'react';
import {
  Box,
  Container,
  VStack,
  Heading,
  Text,
  Button,
  Center,
  Image,
  useColorMode,
  Icon,
  Flex,
} from '@chakra-ui/react';
import { LockIcon } from '@chakra-ui/icons';

const SignIn = () => {
  const [authUrl, setAuthUrl] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const getAuthUrl = async () => {
      try {
        const response = await fetch('http://localhost:9000/oauth/authorize');
        const data = await response.json();
        setAuthUrl(data.auth_url);
      } catch (error) {
        console.error('Failed to get auth URL:', error);
      } finally {
        setLoading(false);
      }
    };

    getAuthUrl();
  }, []);

  const handleGoogleSignIn = () => {
    if (authUrl) {
      const width = 500;
      const height = 600;
      const left = window.screenX + (window.outerWidth - width) / 2;
      const top = window.screenY + (window.outerHeight - height) / 2;

      const popup = window.open(
        authUrl,
        'GoogleSignIn',
        `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
      );

      if (!popup) {
        alert('Please enable pop-ups for this site');
        return;
      }

      popup.focus();

      // Listen for messages from the popup window
      const handleMessage = (event: MessageEvent) => {
        // Verify origin - allow messages from backend OAuth callback
        // The popup will be on localhost:9000 (backend), parent is on localhost:3000
        const isValidOrigin = event.origin === 'http://localhost:9000' || 
                             event.origin === window.location.origin;
        if (!isValidOrigin) {
          console.warn(`Invalid origin: ${event.origin}`);
          return;
        }
        
        if (event.data && event.data.type === 'oauth-complete') {
          window.removeEventListener('message', handleMessage);
          console.log('Received OAuth code, exchanging for token...');
          // Reload the page with the auth code in the URL
          window.location.href = window.location.pathname + '?code=' + event.data.code;
        }
      };

      window.addEventListener('message', handleMessage);

      // Fallback: check if popup closed and reload
      const checkClosed = setInterval(() => {
        try {
          if (popup.closed) {
            clearInterval(checkClosed);
            window.removeEventListener('message', handleMessage);
          }
        } catch (e) {
          clearInterval(checkClosed);
        }
      }, 500);
    }
  };

  return (
    <Box minH="100vh" bg="gray.900">
      <Container maxW="lg" py={{ base: '12', md: '24' }} px={{ base: '0', sm: '6' }}>
        <Center minH="100vh">
          <VStack spacing={8} w="full" align="center">
            {/* Logo and Title */}
            <VStack spacing={4} textAlign="center">
              <Icon as={LockIcon} w={16} h={16} color="brand.500" />
              <Heading as="h1" size="2xl" color="white">
                Email Risk AI
              </Heading>
              <Text fontSize="lg" color="gray.400">
                Detect phishing and suspicious emails with AI
              </Text>
            </VStack>

            {/* Features */}
            <VStack spacing={4} w="full" bg="gray.800" p={8} rounded="lg" border="1px" borderColor="gray.700">
              <Text fontSize="sm" color="gray.300" fontWeight="600" textTransform="uppercase">
                Key Features
              </Text>
              <VStack spacing={3} w="full" align="start" fontSize="sm">
                <Text color="gray.300">✓ Real-time phishing detection</Text>
                <Text color="gray.300">✓ Gmail integration</Text>
                <Text color="gray.300">✓ Risk assessment per email</Text>
                <Text color="gray.300">✓ Dark mode enabled</Text>
              </VStack>
            </VStack>

            {/* Sign In Button */}
            <VStack w="full" spacing={4}>
              <Button
                w="full"
                size="lg"
                bg="brand.600"
                color="white"
                _hover={{ bg: 'brand.700' }}
                isLoading={loading}
                onClick={handleGoogleSignIn}
                leftIcon={
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path
                      fill="currentColor"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="currentColor"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                }
              >
                Continue with Google
              </Button>

              <Text fontSize="xs" color="gray.500" textAlign="center">
                By signing in, you agree to our Terms of Service and Privacy Policy
              </Text>
            </VStack>
          </VStack>
        </Center>
      </Container>
    </Box>
  );
};

export default SignIn;
