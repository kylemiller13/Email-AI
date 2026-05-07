import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  VStack,
  HStack,
  Text,
  Heading,
  Button,
  SimpleGrid,
  Spinner,
  Center,
  Divider,
  List,
  ListItem,
  ListIcon,
  Progress,
} from '@chakra-ui/react';
import {
  CheckCircleIcon,
  WarningTwoIcon,
  ArrowForwardIcon,
  InfoIcon,
} from '@chakra-ui/icons';

interface EmailData {
  subject: string;
  sender: string;
  body: string;
}

interface PairData {
  id: number;
  round: number;
  total_rounds: number;
  theme: string;
  legitimate: EmailData;
  phishing: EmailData;
  red_flags: string[];
  explanation: string;
}

// The two display slots — A and B — are randomly assigned each round
interface DisplaySlot {
  email: EmailData;
  label: 'legitimate' | 'phishing';
}

function shufflePair(pair: PairData): [DisplaySlot, DisplaySlot] {
  const slots: [DisplaySlot, DisplaySlot] = [
    { email: pair.legitimate, label: 'legitimate' },
    { email: pair.phishing,   label: 'phishing'   },
  ];
  return Math.random() < 0.5 ? slots : [slots[1], slots[0]];
}

const EmailPanel = ({
  slot,
  position,
  state,
  onPick,
}: {
  slot: DisplaySlot;
  position: 'A' | 'B';
  state: 'picking' | 'correct' | 'wrong';
  onPick: () => void;
}) => {
  const isPicking = state === 'picking';
  const isRevealed = state !== 'picking';
  const isLegit = slot.label === 'legitimate';

  const borderColor = isRevealed
    ? isLegit
      ? 'green.500'
      : 'red.500'
    : 'gray.600';

  const headerBg = isRevealed
    ? isLegit
      ? 'green.900'
      : 'red.900'
    : 'gray.750';

  return (
    <Box
      bg="gray.800"
      border="2px"
      borderColor={borderColor}
      rounded="xl"
      overflow="hidden"
      transition="border-color 0.3s"
    >
      {/* Reveal banner */}
      {isRevealed && (
        <HStack
          bg={headerBg}
          px={4}
          py={2}
          spacing={2}
          justify="center"
        >
          {isLegit ? (
            <>
              <CheckCircleIcon color="green.300" />
              <Text fontSize="sm" fontWeight="700" color="green.300">
                LEGITIMATE
              </Text>
            </>
          ) : (
            <>
              <WarningTwoIcon color="red.300" />
              <Text fontSize="sm" fontWeight="700" color="red.300">
                PHISHING
              </Text>
            </>
          )}
        </HStack>
      )}

      <VStack align="stretch" spacing={0} p={5}>
        {/* Header label */}
        <Text fontSize="xs" color="gray.500" fontWeight="700" textTransform="uppercase" mb={3}>
          Email {position}
        </Text>

        {/* Email meta */}
        <VStack align="start" spacing={1} mb={4}>
          <HStack>
            <Text fontSize="xs" color="gray.500" w="14">From:</Text>
            <Text fontSize="xs" color="gray.300" fontFamily="mono" wordBreak="break-all">
              {slot.email.sender}
            </Text>
          </HStack>
          <HStack align="start">
            <Text fontSize="xs" color="gray.500" w="14" flexShrink={0}>Subject:</Text>
            <Text fontSize="sm" fontWeight="600" color="gray.100">
              {slot.email.subject}
            </Text>
          </HStack>
        </VStack>

        <Divider borderColor="gray.700" mb={4} />

        {/* Body */}
        <Box
          bg="gray.900"
          rounded="lg"
          p={4}
          mb={5}
          minH="120px"
        >
          <Text fontSize="sm" color="gray.300" whiteSpace="pre-wrap" lineHeight="1.7">
            {slot.email.body}
          </Text>
        </Box>

        {/* Pick button */}
        {isPicking && (
          <Button
            colorScheme="brand"
            variant="outline"
            size="sm"
            onClick={onPick}
            w="full"
          >
            This one is legitimate
          </Button>
        )}
      </VStack>
    </Box>
  );
};

const Compare = () => {
  const [round, setRound] = useState(0);
  const [pair, setPair] = useState<PairData | null>(null);
  const [slots, setSlots] = useState<[DisplaySlot, DisplaySlot] | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<'A' | 'B' | null>(null);
  const [score, setScore] = useState({ correct: 0, total: 0 });

  const loadRound = useCallback(async (r: number) => {
    setLoading(true);
    setSelected(null);
    try {
      const res = await fetch(`http://localhost:9000/compare/pair?round=${r}`);
      if (res.ok) {
        const data: PairData = await res.json();
        setPair(data);
        setSlots(shufflePair(data));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRound(round);
  }, [round, loadRound]);

  if (loading || !pair || !slots) {
    return (
      <Center py={20}>
        <Spinner size="xl" color="brand.500" />
      </Center>
    );
  }

  const totalRounds = pair.total_rounds;
  const isRevealed = selected !== null;

  const handlePick = (position: 'A' | 'B') => {
    if (isRevealed) return;
    const pickedLabel = slots[position === 'A' ? 0 : 1].label;
    const correct = pickedLabel === 'legitimate';
    setSelected(position);
    setScore((s) => ({ correct: s.correct + (correct ? 1 : 0), total: s.total + 1 }));
  };

  const slotAState = (): 'picking' | 'correct' | 'wrong' => {
    if (!isRevealed) return 'picking';
    return slots[0].label === 'legitimate' ? 'correct' : 'wrong';
  };

  const slotBState = (): 'picking' | 'correct' | 'wrong' => {
    if (!isRevealed) return 'picking';
    return slots[1].label === 'legitimate' ? 'correct' : 'wrong';
  };

  const userWasCorrect =
    selected !== null &&
    slots[selected === 'A' ? 0 : 1].label === 'legitimate';

  const isLastRound = round >= totalRounds - 1;

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={8} align="stretch">

        {/* Header */}
        <HStack justify="space-between" align="start" flexWrap="wrap" gap={4}>
          <VStack align="start" spacing={1}>
            <Heading size="lg" color="brand.400">Spot the Phish</Heading>
            <Text color="gray.400" fontSize="sm">
              One of these emails is real. The other is a phishing attempt. Can you tell the difference?
            </Text>
          </VStack>
          <VStack align="end" spacing={1}>
            <Text fontSize="sm" color="gray.400">
              Score: <Text as="span" fontWeight="700" color="white">{score.correct}/{score.total}</Text>
            </Text>
            <Text fontSize="xs" color="gray.500">
              Round {round + 1} of {totalRounds}
            </Text>
          </VStack>
        </HStack>

        {/* Progress bar */}
        <Progress
          value={((round) / totalRounds) * 100}
          size="xs"
          colorScheme="brand"
          rounded="full"
          bg="gray.700"
        />

        {/* Theme prompt */}
        <Box bg="gray.800" p={4} rounded="lg" border="1px" borderColor="gray.700">
          <HStack spacing={3}>
            <InfoIcon color="brand.400" />
            <Text fontSize="sm" color="gray.300">
              <Text as="span" fontWeight="600" color="gray.100">Theme: </Text>
              Both emails are about <Text as="span" fontWeight="600" color="brand.300">{pair.theme}</Text>.
              {!isRevealed && ' Click the one you think is the real, legitimate email.'}
            </Text>
          </HStack>
        </Box>

        {/* Email panels */}
        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
          <EmailPanel
            slot={slots[0]}
            position="A"
            state={slotAState()}
            onPick={() => handlePick('A')}
          />
          <EmailPanel
            slot={slots[1]}
            position="B"
            state={slotBState()}
            onPick={() => handlePick('B')}
          />
        </SimpleGrid>

        {/* Reveal panel */}
        {isRevealed && (
          <VStack spacing={5} align="stretch">

            {/* Result banner */}
            <Box
              bg={userWasCorrect ? 'green.900' : 'red.900'}
              border="1px"
              borderColor={userWasCorrect ? 'green.600' : 'red.600'}
              rounded="xl"
              p={5}
            >
              <HStack spacing={3} mb={2}>
                {userWasCorrect ? (
                  <CheckCircleIcon color="green.300" boxSize={5} />
                ) : (
                  <WarningTwoIcon color="red.300" boxSize={5} />
                )}
                <Heading size="sm" color={userWasCorrect ? 'green.300' : 'red.300'}>
                  {userWasCorrect ? 'Correct! Good eye.' : 'Not quite — that was the phishing email.'}
                </Heading>
              </HStack>
              <Text fontSize="sm" color="gray.300" lineHeight="1.7">
                {pair.explanation}
              </Text>
            </Box>

            {/* Red flags */}
            <Box bg="gray.800" p={5} rounded="xl" border="1px" borderColor="gray.700">
              <Heading size="sm" mb={4} color="orange.300">
                Red flags in the phishing email
              </Heading>
              <List spacing={3}>
                {pair.red_flags.map((flag, i) => (
                  <ListItem key={i} fontSize="sm" color="gray.300">
                    <ListIcon as={WarningTwoIcon} color="orange.400" />
                    {flag}
                  </ListItem>
                ))}
              </List>
            </Box>

            {/* Next / finish */}
            <HStack justify="flex-end">
              {isLastRound ? (
                <VStack align="end" spacing={2}>
                  <Text fontSize="sm" color="gray.400">
                    You finished all rounds! Final score:{' '}
                    <Text as="span" fontWeight="700" color="white">
                      {score.correct}/{score.total}
                    </Text>
                  </Text>
                  <Button
                    colorScheme="brand"
                    rightIcon={<ArrowForwardIcon />}
                    onClick={() => {
                      setScore({ correct: 0, total: 0 });
                      setRound(0);
                    }}
                  >
                    Start Over
                  </Button>
                </VStack>
              ) : (
                <Button
                  colorScheme="brand"
                  rightIcon={<ArrowForwardIcon />}
                  onClick={() => setRound((r) => r + 1)}
                >
                  Next Round
                </Button>
              )}
            </HStack>
          </VStack>
        )}
      </VStack>
    </Container>
  );
};

export default Compare;
