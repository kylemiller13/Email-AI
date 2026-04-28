import { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Heading,
  Badge,
  Button,
  ButtonGroup,
  SimpleGrid,
  Spinner,
  Center,
  Tooltip,
  Divider,
} from '@chakra-ui/react';
import { ArrowUpIcon, ArrowDownIcon, MinusIcon } from '@chakra-ui/icons';

interface DailyStat {
  date: string;
  count: number;
}

interface TopTactic {
  label: string;
  count: number;
}

interface ImpersonatedDomain {
  spoofed: string;
  brand: string;
  real_domain: string | null;
}

interface SummaryData {
  days: number;
  total_threats: number;
  previous_total: number;
  percent_change: number | null;
  trend: 'up' | 'down' | 'same' | 'new';
  daily_breakdown: DailyStat[];
  top_tactic: TopTactic | null;
  impersonated_domains: ImpersonatedDomain[];
}

interface PhishingSummaryProps {
  userEmail: string;
  token: string;
}

const formatDate = (dateStr: string) =>
  new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });

const Sparkline = ({ data }: { data: DailyStat[] }) => {
  const max = Math.max(...data.map((d) => d.count), 1);
  const BAR_MAX_H = 44;
  const BAR_MIN_H = 3;

  return (
    <VStack spacing={1} align="stretch" w="full">
      <HStack spacing="2px" align="flex-end" h={`${BAR_MAX_H}px`} w="full">
        {data.map((d) => {
          const h =
            d.count === 0
              ? BAR_MIN_H
              : Math.max(BAR_MIN_H, Math.round((d.count / max) * BAR_MAX_H));
          const label = `${formatDate(d.date)}: ${d.count} threat${d.count !== 1 ? 's' : ''}`;
          return (
            <Tooltip key={d.date} label={label} placement="top" hasArrow fontSize="xs">
              <Box
                flex={1}
                h={`${h}px`}
                bg={d.count > 0 ? 'red.400' : 'gray.600'}
                rounded="sm"
                cursor="default"
                transition="opacity 0.15s"
                _hover={{ opacity: 0.75 }}
              />
            </Tooltip>
          );
        })}
      </HStack>
      <HStack justify="space-between">
        <Text fontSize="2xs" color="gray.600">
          {formatDate(data[0]?.date ?? '')}
        </Text>
        <Text fontSize="2xs" color="gray.600">
          Today
        </Text>
      </HStack>
    </VStack>
  );
};

const PhishingSummary = ({ userEmail, token }: PhishingSummaryProps) => {
  const [days, setDays] = useState(30);
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const res = await fetch(
          `http://localhost:9000/emails/summary?user_email=${encodeURIComponent(userEmail)}&days=${days}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (res.ok && !cancelled) setSummary(await res.json());
      } catch {
        // summary stays null — handled in render
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [userEmail, token, days]);

  const trendLabel = () => {
    if (!summary) return '';
    const { trend, percent_change, previous_total, days: d } = summary;
    if (trend === 'same' && previous_total === 0) return 'No threats in either period';
    if (trend === 'new') return 'First threats this period';
    if (trend === 'same') return `Same as previous ${d} days`;
    const arrow = trend === 'up' ? '↑' : '↓';
    return `${arrow} ${percent_change}% vs. previous ${d} days`;
  };

  const trendColor =
    summary?.trend === 'up'
      ? 'red.400'
      : summary?.trend === 'down'
      ? 'green.400'
      : 'gray.400';

  const TrendIcon =
    summary?.trend === 'up'
      ? ArrowUpIcon
      : summary?.trend === 'down'
      ? ArrowDownIcon
      : MinusIcon;

  return (
    <Box bg="gray.800" rounded="xl" p={5} border="1px" borderColor="gray.700">
      {/* Header */}
      <HStack justify="space-between" mb={5}>
        <VStack align="start" spacing={0}>
          <Heading size="sm" color="gray.100">
            Phishing Activity Summary
          </Heading>
          <Text fontSize="xs" color="gray.500">
            Patterns and threat levels across your inbox
          </Text>
        </VStack>
        <ButtonGroup size="xs" isAttached>
          <Button
            variant={days === 7 ? 'solid' : 'outline'}
            colorScheme={days === 7 ? 'brand' : undefined}
            borderColor="gray.600"
            onClick={() => setDays(7)}
          >
            7 days
          </Button>
          <Button
            variant={days === 30 ? 'solid' : 'outline'}
            colorScheme={days === 30 ? 'brand' : undefined}
            borderColor="gray.600"
            onClick={() => setDays(30)}
          >
            30 days
          </Button>
        </ButtonGroup>
      </HStack>

      {loading ? (
        <Center py={8}>
          <Spinner color="brand.500" />
        </Center>
      ) : !summary ? (
        <Center py={8}>
          <Text color="gray.500">Could not load summary.</Text>
        </Center>
      ) : (
        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
          {/* ── Total Threats ── */}
          <Box bg="gray.700" p={4} rounded="lg" border="1px" borderColor="gray.600">
            <Text fontSize="xs" color="gray.400" fontWeight="600" textTransform="uppercase" mb={2}>
              Threats Detected
            </Text>
            <HStack spacing={3} align="baseline">
              <Text
                fontSize="4xl"
                fontWeight="bold"
                lineHeight="1"
                color={summary.total_threats > 0 ? 'red.400' : 'green.400'}
              >
                {summary.total_threats}
              </Text>
              <Text fontSize="sm" color="gray.400">
                phishing email{summary.total_threats !== 1 ? 's' : ''}
              </Text>
            </HStack>
            <Text fontSize="xs" color="gray.500" mt={1}>
              in the last {summary.days} days
            </Text>
            {summary.total_threats > 0 || summary.previous_total > 0 ? (
              <HStack mt={3} spacing={1}>
                <TrendIcon color={trendColor} boxSize={3} />
                <Text fontSize="xs" color={trendColor} fontWeight="500">
                  {trendLabel()}
                </Text>
              </HStack>
            ) : (
              <Text fontSize="xs" color="green.400" mt={3}>
                Your inbox looks clean for this period.
              </Text>
            )}
          </Box>

          {/* ── Daily Trend Sparkline ── */}
          <Box bg="gray.700" p={4} rounded="lg" border="1px" borderColor="gray.600">
            <Text fontSize="xs" color="gray.400" fontWeight="600" textTransform="uppercase" mb={3}>
              Daily Threat Trend
            </Text>
            <Sparkline data={summary.daily_breakdown} />
          </Box>

          {/* ── Most Common Tactic ── */}
          <Box bg="gray.700" p={4} rounded="lg" border="1px" borderColor="gray.600">
            <Text fontSize="xs" color="gray.400" fontWeight="600" textTransform="uppercase" mb={3}>
              Most Common Attack Tactic
            </Text>
            {summary.top_tactic ? (
              <VStack align="start" spacing={2}>
                <Badge colorScheme="orange" fontSize="sm" px={2} py={1} rounded="md">
                  {summary.top_tactic.label}
                </Badge>
                <Text fontSize="xs" color="gray.400">
                  Detected {summary.top_tactic.count} time
                  {summary.top_tactic.count !== 1 ? 's' : ''} across{' '}
                  {summary.total_threats} threatening email
                  {summary.total_threats !== 1 ? 's' : ''}.
                </Text>
                <Divider borderColor="gray.600" />
                <Text fontSize="xs" color="gray.500">
                  {summary.top_tactic.label === 'Urgency & Pressure' &&
                    'Attackers create a false sense of urgency to make you act before thinking.'}
                  {summary.top_tactic.label === 'Credential Harvesting' &&
                    'Emails designed to trick you into entering your password or personal details.'}
                  {summary.top_tactic.label === 'Malicious Links' &&
                    'Links that lead to fake or dangerous websites.'}
                  {summary.top_tactic.label === 'Impersonation' &&
                    'Emails pretending to be from someone or a brand you trust.'}
                  {summary.top_tactic.label === 'Financial Scam' &&
                    'Fake prize, lottery, or money transfer offers.'}
                  {summary.top_tactic.label === 'Spoofed Sender' &&
                    'The sender address is designed to look legitimate but isn\'t.'}
                  {summary.top_tactic.label === 'Aggressive Formatting' &&
                    'Excessive caps or exclamation marks used to pressure you.'}
                  {summary.top_tactic.label === 'Malicious Attachment' &&
                    'Emails urging you to open a file that may contain malware.'}
                  {summary.top_tactic.label === 'Technical Attack' &&
                    'Emails using scripts or code to run malicious actions.'}
                </Text>
              </VStack>
            ) : (
              <Text fontSize="sm" color="green.400">
                No attack tactics detected in this period.
              </Text>
            )}
          </Box>

          {/* ── Impersonated Brands ── */}
          <Box bg="gray.700" p={4} rounded="lg" border="1px" borderColor="gray.600">
            <Text fontSize="xs" color="gray.400" fontWeight="600" textTransform="uppercase" mb={3}>
              Brands Being Impersonated
            </Text>
            {summary.impersonated_domains.length > 0 ? (
              <VStack align="start" spacing={3} divider={<Divider borderColor="gray.600" />}>
                {summary.impersonated_domains.map((imp, idx) => (
                  <HStack key={idx} justify="space-between" w="full">
                    <VStack align="start" spacing={0}>
                      <Text fontSize="sm" color="red.300" fontWeight="600">
                        {imp.brand}
                      </Text>
                      {imp.real_domain && (
                        <Text fontSize="xs" color="gray.500">
                          Real domain: {imp.real_domain}
                        </Text>
                      )}
                    </VStack>
                    <VStack align="end" spacing={0}>
                      <Text fontSize="xs" color="gray.400" fontFamily="mono">
                        {imp.spoofed}
                      </Text>
                      <Badge colorScheme="red" fontSize="2xs">
                        fake
                      </Badge>
                    </VStack>
                  </HStack>
                ))}
                <Text fontSize="xs" color="gray.500" pt={1}>
                  These senders are pretending to be trusted brands. Do not click any links in these emails.
                </Text>
              </VStack>
            ) : (
              <Text fontSize="sm" color="green.400">
                No brand impersonation detected in this period.
              </Text>
            )}
          </Box>
        </SimpleGrid>
      )}
    </Box>
  );
};

export default PhishingSummary;
