import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  VStack,
  HStack,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Heading,
  Text,
  Badge,
  Button,
  Spinner,
  Center,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  useToast,
  Divider,
} from '@chakra-ui/react';
import { RepeatIcon, WarningIcon, CheckCircleIcon } from '@chakra-ui/icons';

interface Metrics {
  total_analyzed: number;
  phishing_count: number;
  legitimate_count: number;
  false_positives: number;
  false_negatives: number;
}

interface FeedbackEntry {
  id: number;
  email_id: number;
  sender: string;
  subject: string;
  user_correction: string;
  reported_at: string;
  notes: string | null;
  original_classification: string;
  original_risk_level: string;
}

interface AdminProps {
  token: string;
  userEmail: string;
}

const Admin = ({ token, userEmail }: AdminProps) => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [feedback, setFeedback] = useState<FeedbackEntry[]>([]);
  const [loadingMetrics, setLoadingMetrics] = useState(true);
  const [loadingFeedback, setLoadingFeedback] = useState(true);
  const [retraining, setRetraining] = useState(false);
  const [retrainOutput, setRetrainOutput] = useState<string | null>(null);
  const toast = useToast();

  const headers = { Authorization: `Bearer ${token}` };

  const fetchMetrics = useCallback(async () => {
    setLoadingMetrics(true);
    try {
      const res = await fetch(`http://localhost:9000/admin/metrics?user_email=${encodeURIComponent(userEmail)}`, { headers });
      if (res.ok) setMetrics(await res.json());
    } catch (e) {
      console.error('Failed to fetch metrics', e);
    } finally {
      setLoadingMetrics(false);
    }
  }, [token]);

  const fetchFeedback = useCallback(async () => {
    setLoadingFeedback(true);
    try {
      const res = await fetch(`http://localhost:9000/admin/feedback?user_email=${encodeURIComponent(userEmail)}`, { headers });
      if (res.ok) setFeedback(await res.json());
    } catch (e) {
      console.error('Failed to fetch feedback', e);
    } finally {
      setLoadingFeedback(false);
    }
  }, [token]);

  useEffect(() => {
    fetchMetrics();
    fetchFeedback();
  }, [fetchMetrics, fetchFeedback]);

  const handleRetrain = async () => {
    setRetraining(true);
    setRetrainOutput(null);
    try {
      const res = await fetch('http://localhost:9000/admin/retrain', {
        method: 'POST',
        headers,
      });
      const data = await res.json();
      if (res.ok) {
        setRetrainOutput(data.output || 'Training complete.');
        toast({
          title: 'Model retrained successfully',
          status: 'success',
          duration: 4000,
          isClosable: true,
        });
        fetchMetrics();
      } else {
        throw new Error(data.detail || 'Retrain failed');
      }
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : 'Unknown error';
      toast({
        title: 'Retrain failed',
        description: message,
        status: 'error',
        duration: 6000,
        isClosable: true,
      });
    } finally {
      setRetraining(false);
    }
  };

  const phishingRate =
    metrics && metrics.total_analyzed > 0
      ? ((metrics.phishing_count / metrics.total_analyzed) * 100).toFixed(1)
      : '0';

  const errorRate =
    metrics && metrics.total_analyzed > 0
      ? (
          ((metrics.false_positives + metrics.false_negatives) /
            metrics.total_analyzed) *
          100
        ).toFixed(1)
      : '0';

  const falsePositives = feedback.filter(
    (f) => f.user_correction === 'legitimate' && f.original_classification === 'phishing'
  );
  const falseNegatives = feedback.filter(
    (f) => f.user_correction === 'phishing' && f.original_classification === 'legitimate'
  );

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={8} align="stretch">

        {/* Header */}
        <HStack justify="space-between" align="center">
          <VStack align="start" spacing={0}>
            <Heading size="lg" color="brand.400">Admin Panel</Heading>
            <Text fontSize="sm" color="gray.400">Model performance, feedback logs, and retraining</Text>
          </VStack>
          <Button
            leftIcon={<RepeatIcon />}
            onClick={() => { fetchMetrics(); fetchFeedback(); }}
            variant="outline"
            size="sm"
          >
            Refresh
          </Button>
        </HStack>

        <Divider borderColor="gray.700" />

        {/* Metrics */}
        <Box>
          <Heading size="md" mb={4}>Detection Metrics</Heading>
          {loadingMetrics ? (
            <Center py={8}><Spinner color="brand.500" /></Center>
          ) : metrics ? (
            <SimpleGrid columns={{ base: 2, md: 5 }} spacing={4}>
              <Box bg="gray.800" p={5} rounded="lg" border="1px" borderColor="gray.700">
                <Stat>
                  <StatLabel color="gray.400">Total Analyzed</StatLabel>
                  <StatNumber color="white">{metrics.total_analyzed}</StatNumber>
                  <StatHelpText color="gray.500">all time</StatHelpText>
                </Stat>
              </Box>
              <Box bg="gray.800" p={5} rounded="lg" border="1px" borderColor="red.800">
                <Stat>
                  <StatLabel color="gray.400">Phishing</StatLabel>
                  <StatNumber color="red.400">{metrics.phishing_count}</StatNumber>
                  <StatHelpText color="gray.500">{phishingRate}% of total</StatHelpText>
                </Stat>
              </Box>
              <Box bg="gray.800" p={5} rounded="lg" border="1px" borderColor="green.800">
                <Stat>
                  <StatLabel color="gray.400">Legitimate</StatLabel>
                  <StatNumber color="green.400">{metrics.legitimate_count}</StatNumber>
                  <StatHelpText color="gray.500">{(100 - parseFloat(phishingRate)).toFixed(1)}% of total</StatHelpText>
                </Stat>
              </Box>
              <Box bg="gray.800" p={5} rounded="lg" border="1px" borderColor="orange.800">
                <Stat>
                  <StatLabel color="gray.400">False Positives</StatLabel>
                  <StatNumber color="orange.400">{metrics.false_positives}</StatNumber>
                  <StatHelpText color="gray.500">flagged incorrectly</StatHelpText>
                </Stat>
              </Box>
              <Box bg="gray.800" p={5} rounded="lg" border="1px" borderColor="yellow.800">
                <Stat>
                  <StatLabel color="gray.400">False Negatives</StatLabel>
                  <StatNumber color="yellow.400">{metrics.false_negatives}</StatNumber>
                  <StatHelpText color="gray.500">missed phishing</StatHelpText>
                </Stat>
              </Box>
            </SimpleGrid>
          ) : (
            <Text color="gray.500">Could not load metrics.</Text>
          )}

          {metrics && parseFloat(errorRate) > 10 && (
            <Alert status="warning" mt={4} rounded="lg" bg="orange.900" borderColor="orange.700" border="1px">
              <AlertIcon />
              <AlertTitle>High error rate</AlertTitle>
              <AlertDescription>
                {errorRate}% of analyzed emails have been flagged as incorrect by users. Consider retraining the model.
              </AlertDescription>
            </Alert>
          )}
        </Box>

        <Divider borderColor="gray.700" />

        {/* Retrain */}
        <Box>
          <Heading size="md" mb={2}>Model Retraining</Heading>
          <Text fontSize="sm" color="gray.400" mb={4}>
            Triggers <Text as="code" fontSize="xs" bg="gray.700" px={1} rounded="sm">python3 -m ml.train</Text> on the server.
            The new model replaces <Text as="code" fontSize="xs" bg="gray.700" px={1} rounded="sm">ml/model.pkl</Text> immediately.
          </Text>
          <Button
            colorScheme="brand"
            leftIcon={<RepeatIcon />}
            onClick={handleRetrain}
            isLoading={retraining}
            loadingText="Training… this may take a minute"
          >
            Retrain Model
          </Button>

          {retrainOutput && (
            <Box
              mt={4}
              bg="gray.900"
              border="1px"
              borderColor="gray.600"
              rounded="lg"
              p={4}
              maxH="200px"
              overflowY="auto"
            >
              <Text fontSize="xs" fontFamily="mono" color="green.300" whiteSpace="pre-wrap">
                {retrainOutput}
              </Text>
            </Box>
          )}
        </Box>

        <Divider borderColor="gray.700" />

        {/* Feedback log */}
        <Box>
          <HStack justify="space-between" mb={4}>
            <Heading size="md">User Feedback Log</Heading>
            <HStack spacing={3}>
              <Badge colorScheme="orange" px={2} py={1} rounded="full">
                {falsePositives.length} false positives
              </Badge>
              <Badge colorScheme="yellow" px={2} py={1} rounded="full">
                {falseNegatives.length} false negatives
              </Badge>
            </HStack>
          </HStack>

          {loadingFeedback ? (
            <Center py={8}><Spinner color="brand.500" /></Center>
          ) : feedback.length === 0 ? (
            <Box bg="gray.800" p={6} rounded="lg" border="1px" borderColor="gray.700" textAlign="center">
              <CheckCircleIcon color="green.400" boxSize={6} mb={2} />
              <Text color="gray.400">No user corrections submitted yet.</Text>
            </Box>
          ) : (
            <TableContainer bg="gray.800" rounded="lg" border="1px" borderColor="gray.700">
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th color="gray.400" borderColor="gray.700">Sender</Th>
                    <Th color="gray.400" borderColor="gray.700">Subject</Th>
                    <Th color="gray.400" borderColor="gray.700">Model said</Th>
                    <Th color="gray.400" borderColor="gray.700">User says</Th>
                    <Th color="gray.400" borderColor="gray.700">Type</Th>
                    <Th color="gray.400" borderColor="gray.700">Reported</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {feedback.map((entry) => {
                    const isFP =
                      entry.user_correction === 'legitimate' &&
                      entry.original_classification === 'phishing';
                    const isFN =
                      entry.user_correction === 'phishing' &&
                      entry.original_classification === 'legitimate';
                    return (
                      <Tr key={entry.id} _hover={{ bg: 'gray.750' }}>
                        <Td borderColor="gray.700" maxW="160px" isTruncated color="gray.300" fontSize="xs">
                          {entry.sender}
                        </Td>
                        <Td borderColor="gray.700" maxW="200px" isTruncated color="gray.300" fontSize="xs">
                          {entry.subject}
                        </Td>
                        <Td borderColor="gray.700">
                          <Badge
                            colorScheme={entry.original_classification === 'phishing' ? 'red' : 'green'}
                            fontSize="xs"
                          >
                            {entry.original_classification}
                          </Badge>
                        </Td>
                        <Td borderColor="gray.700">
                          <Badge
                            colorScheme={entry.user_correction === 'phishing' ? 'red' : 'green'}
                            fontSize="xs"
                          >
                            {entry.user_correction}
                          </Badge>
                        </Td>
                        <Td borderColor="gray.700">
                          {isFP && (
                            <HStack spacing={1}>
                              <WarningIcon color="orange.400" boxSize={3} />
                              <Text fontSize="xs" color="orange.400">False Positive</Text>
                            </HStack>
                          )}
                          {isFN && (
                            <HStack spacing={1}>
                              <WarningIcon color="yellow.400" boxSize={3} />
                              <Text fontSize="xs" color="yellow.400">False Negative</Text>
                            </HStack>
                          )}
                        </Td>
                        <Td borderColor="gray.700" color="gray.500" fontSize="xs">
                          {new Date(entry.reported_at).toLocaleDateString()}
                        </Td>
                      </Tr>
                    );
                  })}
                </Tbody>
              </Table>
            </TableContainer>
          )}
        </Box>

      </VStack>
    </Container>
  );
};

export default Admin;
