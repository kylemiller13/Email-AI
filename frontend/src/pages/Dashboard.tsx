import { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Container,
  VStack,
  HStack,
  Button,
  Spinner,
  Center,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  SimpleGrid,
  Input,
  InputGroup,
  InputLeftElement,
  InputRightElement,
  IconButton,
  Text,
} from '@chakra-ui/react';
import { SearchIcon, CloseIcon } from '@chakra-ui/icons';
import EmailCard from '../components/EmailCard';
import EmailDetailModal from '../components/EmailDetailModal';
import PhishingSummary from '../components/PhishingSummary';

interface Email {
  id: string;
  subject: string;
  from: string;
  risk_score: number;
  risk_level: string;
  indicators: string[];
  timestamp: string;
}

const RISK_LEVEL_MAP: Record<string, string> = {
  high: 'critical',
  medium: 'warning',
  low: 'safe',
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const normalizeEmail = (raw: any): Email => {
  const rawLevel = raw.risk_level ?? 'unknown';
  return {
    id: String(raw.email_id ?? raw.id ?? ''),
    subject: raw.subject ?? '(no subject)',
    from: raw.sender ?? raw.from ?? '',
    risk_score: raw.confidence_score ?? raw.risk_score ?? 0,
    risk_level: RISK_LEVEL_MAP[rawLevel] ?? rawLevel,
    indicators: raw.warning_signs ?? raw.indicators ?? [],
    timestamp: raw.received_at ?? raw.timestamp ?? '',
  };
};

interface DashboardProps {
  userEmail: string;
  token: string;
}

const Dashboard = ({ userEmail, token }: DashboardProps) => {
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchEmails = async () => {
    setLoading(true);
    try {
      // Pull new emails from Gmail and analyze them
      await fetch(
        `http://localhost:9000/emails/fetch-from-gmail?user_email=${encodeURIComponent(userEmail)}`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` } }
      );

      // Load all analyzed emails from the database
      const response = await fetch(
        `http://localhost:9000/emails?user_email=${encodeURIComponent(userEmail)}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (response.ok) {
        const data = await response.json();
        const raw = Array.isArray(data) ? data : data.emails ?? [];
        setEmails(raw.map(normalizeEmail));
      }
    } catch (error) {
      console.error('Failed to fetch emails:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmails();
  }, []);

  const filteredEmails = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return emails;
    return emails.filter(
      (e) =>
        e.subject.toLowerCase().includes(q) ||
        e.from.toLowerCase().includes(q)
    );
  }, [emails, searchQuery]);

  const criticalEmails = filteredEmails.filter((e) => e.risk_level === 'critical');
  const warningEmails = filteredEmails.filter((e) => e.risk_level === 'warning');
  const safeEmails = filteredEmails.filter((e) => e.risk_level === 'safe');

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={8} align="stretch">
        {/* Action Bar */}
        <HStack justify="space-between">
          <Button
            colorScheme="brand"
            size="lg"
            onClick={fetchEmails}
            isLoading={loading}
          >
            {loading ? 'Fetching Emails...' : 'Fetch & Analyze Emails'}
          </Button>
        </HStack>

        {/* Phishing Activity Summary */}
        <PhishingSummary userEmail={userEmail} token={token} />

        {/* Search */}
        {emails.length > 0 && (
          <InputGroup>
            <InputLeftElement pointerEvents="none">
              <SearchIcon color="gray.400" />
            </InputLeftElement>
            <Input
              placeholder="Search by subject or sender…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              bg="gray.800"
              borderColor="gray.600"
              _hover={{ borderColor: 'gray.500' }}
              _focus={{ borderColor: 'brand.500', boxShadow: 'none' }}
            />
            {searchQuery && (
              <InputRightElement>
                <IconButton
                  aria-label="Clear search"
                  icon={<CloseIcon boxSize={2.5} />}
                  size="xs"
                  variant="ghost"
                  onClick={() => setSearchQuery('')}
                />
              </InputRightElement>
            )}
          </InputGroup>
        )}

        {/* Email Tabs */}
        {emails.length > 0 ? (
          <Tabs variant="soft-rounded" colorScheme="brand">
            <TabList mb={4}>
              <Tab>
                All ({filteredEmails.length}{searchQuery ? ` of ${emails.length}` : ''})
              </Tab>
              <Tab color="semantic.critical">
                Critical ({criticalEmails.length})
              </Tab>
              <Tab color="semantic.warning">
                Warnings ({warningEmails.length})
              </Tab>
              <Tab color="semantic.safe">
                Safe ({safeEmails.length})
              </Tab>
            </TabList>

            <TabPanels>
              {/* All Emails */}
              <TabPanel>
                {filteredEmails.length === 0 ? (
                  <Center py={12}>
                    <Text color="gray.500">No emails match &quot;{searchQuery}&quot;</Text>
                  </Center>
                ) : (
                  <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
                    {filteredEmails.map((email) => (
                      <EmailCard
                        key={email.id}
                        email={email}
                        onClick={() => setSelectedEmail(email)}
                      />
                    ))}
                  </SimpleGrid>
                )}
              </TabPanel>

              {/* Critical Emails */}
              <TabPanel>
                {criticalEmails.length === 0 ? (
                  <Center py={12}>
                    <Text color="gray.500">
                      {searchQuery ? `No critical emails match "${searchQuery}"` : 'No critical emails'}
                    </Text>
                  </Center>
                ) : (
                  <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
                    {criticalEmails.map((email) => (
                      <EmailCard
                        key={email.id}
                        email={email}
                        onClick={() => setSelectedEmail(email)}
                      />
                    ))}
                  </SimpleGrid>
                )}
              </TabPanel>

              {/* Warning Emails */}
              <TabPanel>
                {warningEmails.length === 0 ? (
                  <Center py={12}>
                    <Text color="gray.500">
                      {searchQuery ? `No warning emails match "${searchQuery}"` : 'No warning emails'}
                    </Text>
                  </Center>
                ) : (
                  <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
                    {warningEmails.map((email) => (
                      <EmailCard
                        key={email.id}
                        email={email}
                        onClick={() => setSelectedEmail(email)}
                      />
                    ))}
                  </SimpleGrid>
                )}
              </TabPanel>

              {/* Safe Emails */}
              <TabPanel>
                {safeEmails.length === 0 ? (
                  <Center py={12}>
                    <Text color="gray.500">
                      {searchQuery ? `No safe emails match "${searchQuery}"` : 'No safe emails'}
                    </Text>
                  </Center>
                ) : (
                  <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
                    {safeEmails.map((email) => (
                      <EmailCard
                        key={email.id}
                        email={email}
                        onClick={() => setSelectedEmail(email)}
                      />
                    ))}
                  </SimpleGrid>
                )}
              </TabPanel>
            </TabPanels>
          </Tabs>
        ) : loading ? (
          <Center py={12}>
            <Spinner size="xl" color="brand.500" />
          </Center>
        ) : (
          <Center py={12}>
            <Box textAlign="center">
              <p>No emails fetched yet. Click "Fetch & Analyze Emails" to get started.</p>
            </Box>
          </Center>
        )}

        {/* Email Detail Modal */}
        {selectedEmail && (
          <EmailDetailModal
            email={selectedEmail}
            isOpen={!!selectedEmail}
            onClose={() => setSelectedEmail(null)}
          />
        )}
      </VStack>
    </Container>
  );
};

export default Dashboard;
