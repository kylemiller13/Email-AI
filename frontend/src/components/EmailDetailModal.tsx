import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Button,
  VStack,
  HStack,
  Text,
  Divider,
  Box,
  Heading,
  List,
  ListItem,
  ListIcon,
} from '@chakra-ui/react';
import { WarningIcon, CheckCircleIcon, WarningTwoIcon } from '@chakra-ui/icons';

interface Email {
  id: string;
  subject: string;
  from: string;
  risk_score: number;
  risk_level: string;
  indicators: string[];
  timestamp: string;
}

interface EmailDetailModalProps {
  email: Email | null;
  isOpen: boolean;
  onClose: () => void;
}

const EmailDetailModal = ({ email, isOpen, onClose }: EmailDetailModalProps) => {
  if (!email) return null;

  const getRiskIcon = (level: string) => {
    switch (level) {
      case 'critical':
        return <WarningTwoIcon color="semantic.critical" />;
      case 'warning':
        return <WarningIcon color="semantic.warning" />;
      case 'safe':
        return <CheckCircleIcon color="semantic.safe" />;
      default:
        return null;
    }
  };

  const riskDescription: Record<string, string> = {
    critical: 'This email shows strong indicators of phishing or malicious intent. Do not click any links or download attachments.',
    warning: 'This email has some suspicious characteristics. Exercise caution before interacting.',
    caution: 'This email has minor warning signs. Review carefully before proceeding.',
    safe: 'This email appears to be legitimate based on our analysis.',
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="2xl">
      <ModalOverlay />
      <ModalContent bg="gray.800" borderColor="gray.700" borderWidth="1px">
        <ModalHeader>Email Details</ModalHeader>
        <ModalCloseButton />

        <ModalBody>
          <VStack spacing={6} align="stretch">
            {/* Risk Assessment */}
            <Box bg="gray.700" p={6} rounded="lg" borderLeft="4px" borderColor={`semantic.${email.risk_level === 'critical' ? 'critical' : email.risk_level === 'warning' ? 'warning' : email.risk_level === 'safe' ? 'safe' : 'caution'}`}>
              <HStack spacing={4} mb={3}>
                {getRiskIcon(email.risk_level)}
                <Heading size="md" textTransform="capitalize">
                  {email.risk_level} Risk
                </Heading>
              </HStack>
              <Text fontSize="sm" color="gray.300" mb={3}>
                Risk Score: <strong>{Math.round(email.risk_score * 100)}%</strong>
              </Text>
              <Text fontSize="sm" color="gray.300">
                {riskDescription[email.risk_level]}
              </Text>
            </Box>

            <Divider borderColor="gray.600" />

            {/* Email Info */}
            <VStack align="start" spacing={3} w="full">
              <VStack align="start" w="full" spacing={1}>
                <Text fontSize="xs" color="gray.500" fontWeight="600" textTransform="uppercase">
                  From
                </Text>
                <Text fontSize="sm" wordBreak="break-all">
                  {email.from}
                </Text>
              </VStack>

              <VStack align="start" w="full" spacing={1}>
                <Text fontSize="xs" color="gray.500" fontWeight="600" textTransform="uppercase">
                  Subject
                </Text>
                <Text fontSize="sm">{email.subject}</Text>
              </VStack>

              <VStack align="start" w="full" spacing={1}>
                <Text fontSize="xs" color="gray.500" fontWeight="600" textTransform="uppercase">
                  Date
                </Text>
                <Text fontSize="sm">
                  {new Date(email.timestamp).toLocaleString()}
                </Text>
              </VStack>
            </VStack>

            <Divider borderColor="gray.600" />

            {/* Risk Indicators */}
            {email.indicators.length > 0 && (
              <VStack align="start" w="full" spacing={3}>
                <Heading size="sm">Detected Risk Indicators</Heading>
                <List spacing={2}>
                  {email.indicators.map((indicator, idx) => (
                    <ListItem key={idx} fontSize="sm">
                      <ListIcon as={WarningTwoIcon} color="semantic.warning" mr={2} />
                      {indicator}
                    </ListItem>
                  ))}
                </List>
              </VStack>
            )}

            {/* Recommendations */}
            <Box bg="gray.700" p={4} rounded="lg">
              <Heading size="sm" mb={3}>
                Recommendations
              </Heading>
              <List spacing={2} fontSize="sm">
                {email.risk_level === 'critical' && (
                  <>
                    <ListItem>
                      <ListIcon as={WarningTwoIcon} color="semantic.critical" />
                      Do not click any links or download attachments
                    </ListItem>
                    <ListItem>
                      <ListIcon as={WarningTwoIcon} color="semantic.critical" />
                      Report this email as phishing/spam
                    </ListItem>
                    <ListItem>
                      <ListIcon as={WarningTwoIcon} color="semantic.critical" />
                      Delete the email
                    </ListItem>
                  </>
                )}
                {email.risk_level === 'warning' && (
                  <>
                    <ListItem>
                      <ListIcon as={WarningIcon} color="semantic.warning" />
                      Exercise caution with any links or attachments
                    </ListItem>
                    <ListItem>
                      <ListIcon as={WarningIcon} color="semantic.warning" />
                      Verify sender identity through alternative means
                    </ListItem>
                  </>
                )}
                {email.risk_level === 'safe' && (
                  <ListItem>
                    <ListIcon as={CheckCircleIcon} color="semantic.safe" />
                    This email appears to be legitimate
                  </ListItem>
                )}
              </List>
            </Box>
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button colorScheme="brand" onClick={onClose}>
            Close
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default EmailDetailModal;
