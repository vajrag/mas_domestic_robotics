import rospy

from std_msgs.msg import String

from mas_execution_manager.scenario_state_base import ScenarioStateBase

class WaitForQR(ScenarioStateBase):
    def __init__(self, save_sm_state=False, **kwargs):
        ScenarioStateBase.__init__(self, 'wait_for_qr',
                                   save_sm_state=save_sm_state,
                                   outcomes=['succeeded', 'waiting', 'failed'],
                                   output_keys=['command'])
        self.timeout = rospy.Duration.from_sec(kwargs.get('timeout', 120.))
        self.state_check_rate = rospy.Rate(5)
        self.qr_code_sub = rospy.Subscriber(kwargs.get('qr_topic',
                                                       '/mcr_perception/qr_reader/output'),
                                            String, self.register_qr_code)
        self.qr_message = None

        self.start_time = rospy.Time.now()
        self.restart_state = False
        self.asked_for_qr = False

    def execute(self, userdata):
        if self.restart_state:
            self.start_time = rospy.Time.now()
            self.restart_state = False
            self.say('Please show me a continue QR code')

        if not self.asked_for_qr:
            self.say('Please show me a continue QR code')
            self.asked_for_qr = True

        if (rospy.Time.now() - self.start_time) < self.timeout:
            if self.qr_message and "continue" in self.qr_message.lower():
                rospy.loginfo('QR message: %s' % self.qr_message)
                self.say('Continuing operation')
                userdata.command = self.qr_message
                self.restart_state = True
                return 'succeeded'

            self.state_check_rate.sleep()
            rospy.loginfo('Waiting for QR code')
            return 'waiting'

        rospy.loginfo('wait_for_qr timed out')
        self.restart_state = True
        return 'failed'

    def register_qr_code(self, msg):
        self.qr_message = msg.data
