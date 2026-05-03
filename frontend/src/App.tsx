import { useState, useEffect } from 'react';
import {
  Box,
  Container,
  VStack,
  HStack,
  Button,
  Text,
  Heading,
  useColorMode,
  IconButton,
  Drawer,
  DrawerBody,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  useDisclosure,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Avatar,
  Spinner,
  Center,
} from '@chakra-ui/react';
import { MoonIcon, SunIcon, HamburgerIcon } from '@chakra-ui/icons';
import Dashboard from './pages/Dashboard';
import Admin from './pages/Admin';
import SignIn from './pages/SignIn';

interface AuthState {
  isAuthenticated: boolean;
  userEmail: string | null;
  token: string | null;
}

function App() {
  const { colorMode, toggleColorMode } = useColorMode();
  const [auth, setAuth] = useState<AuthState>({
    isAuthenticated: false,
    userEmail: null,
    token: null,
  });
  const [loading, setLoading] = useState(true);
  const [activePage, setActivePage] = useState<'dashboard' | 'admin'>('dashboard');
  const { isOpen, onOpen, onClose } = useDisclosure();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Restore session from localStorage first
        const storedToken = localStorage.getItem('auth_token');
        const storedEmail = localStorage.getItem('auth_email');
        if (storedToken && storedEmail) {
          setAuth({ isAuthenticated: true, userEmail: storedEmail, token: storedToken });
          setLoading(false);
          return;
        }

        const params = new URLSearchParams(window.location.search);
        const code = params.get('code');

        if (code) {
          // Clean up URL immediately so a refresh won't re-use the code
          window.history.replaceState({}, document.title, window.location.pathname);

          const response = await fetch('http://localhost:9000/oauth/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code }),
          });

          if (response.ok) {
            const data = await response.json();
            localStorage.setItem('auth_token', data.access_token);
            localStorage.setItem('auth_email', data.email);
            setAuth({ isAuthenticated: true, userEmail: data.email, token: data.access_token });
          } else {
            const errorData = await response.json();
            console.error('Token exchange failed:', errorData);
            alert(`Authentication failed: ${errorData.detail || 'Unknown error'}`);
          }
        }
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_email');
    setAuth({ isAuthenticated: false, userEmail: null, token: null });
  };

  if (loading) {
    return (
      <Center h="100vh">
        <Spinner size="xl" color="brand.500" />
      </Center>
    );
  }

  if (!auth.isAuthenticated) {
    return <SignIn />;
  }

  return (
    <Box minH="100vh" bg="gray.900">
      {/* Header */}
      <Box bg="gray.800" borderBottom="1px" borderColor="gray.700" py={4}>
        <Container maxW="container.xl">
          <HStack justify="space-between">
            <HStack spacing={6}>
              <Heading size="lg" color="brand.400">
                🛡️ Email Risk AI
              </Heading>
              <HStack spacing={1} display={{ base: 'none', md: 'flex' }}>
                <Button
                  variant={activePage === 'dashboard' ? 'solid' : 'ghost'}
                  colorScheme={activePage === 'dashboard' ? 'brand' : undefined}
                  size="sm"
                  onClick={() => setActivePage('dashboard')}
                >
                  Dashboard
                </Button>
                <Button
                  variant={activePage === 'admin' ? 'solid' : 'ghost'}
                  colorScheme={activePage === 'admin' ? 'brand' : undefined}
                  size="sm"
                  onClick={() => setActivePage('admin')}
                >
                  Admin
                </Button>
              </HStack>
            </HStack>

            <HStack spacing={4} display={{ base: 'none', md: 'flex' }}>
              <IconButton
                aria-label="Toggle color mode"
                icon={colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
                onClick={toggleColorMode}
                variant="ghost"
              />

              <Menu>
                <MenuButton as={Button} variant="ghost">
                  <Avatar name={auth.userEmail || 'User'} size="sm" />
                </MenuButton>
                <MenuList>
                  <MenuItem isDisabled>
                    <Text fontSize="sm">{auth.userEmail}</Text>
                  </MenuItem>
                  <MenuItem onClick={handleLogout} color="semantic.critical">
                    Sign Out
                  </MenuItem>
                </MenuList>
              </Menu>
            </HStack>

            {/* Mobile menu */}
            <HStack display={{ base: 'flex', md: 'none' }} spacing={2}>
              <IconButton
                aria-label="Toggle color mode"
                icon={colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
                onClick={toggleColorMode}
                variant="ghost"
              />
              <IconButton
                aria-label="Open menu"
                icon={<HamburgerIcon />}
                onClick={onOpen}
                variant="ghost"
              />
            </HStack>
          </HStack>
        </Container>
      </Box>

      {/* Mobile Drawer */}
      <Drawer isOpen={isOpen} placement="right" onClose={onClose}>
        <DrawerOverlay />
        <DrawerContent bg="gray.800">
          <DrawerCloseButton />
          <DrawerBody pt={8}>
            <VStack spacing={4} align="stretch">
              <Text>{auth.userEmail}</Text>
              <Button
                variant={activePage === 'dashboard' ? 'solid' : 'ghost'}
                colorScheme="brand"
                onClick={() => { setActivePage('dashboard'); onClose(); }}
                w="full"
              >
                Dashboard
              </Button>
              <Button
                variant={activePage === 'admin' ? 'solid' : 'ghost'}
                colorScheme="brand"
                onClick={() => { setActivePage('admin'); onClose(); }}
                w="full"
              >
                Admin
              </Button>
              <Button colorScheme="red" onClick={handleLogout} w="full">
                Sign Out
              </Button>
            </VStack>
          </DrawerBody>
        </DrawerContent>
      </Drawer>

      {/* Main Content */}
      {activePage === 'dashboard' ? (
        <Dashboard userEmail={auth.userEmail || ''} token={auth.token || ''} onSessionExpired={handleLogout} />
      ) : (
        <Admin token={auth.token || ''} userEmail={auth.userEmail || ''} />
      )}
    </Box>
  );
}

export default App;
